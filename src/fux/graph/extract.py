"""Deterministic edge extraction and node payloads (handoff 0004 M3).

Four edge kinds, each read off an artifact the corpus already contains:

| kind | read from | meaning |
|------|-----------|---------|
| `references` | markdown links | this doc points at that one |
| `cites` | links inside a citations/references section | this doc's claim rests on that one |
| `crawled_from` | the crawl's recorded parent | this page was reached from that one |
| `tagged` | frontmatter `tags` | this doc belongs to that tag |

`cites` is deliberately separated from `references`: a link in a Citations
section is evidence, and evidence should outrank a passing mention when the
expansion later scores paths.

Tags become their own nodes (`tag:<name>`) rather than doc↔doc edges. With N
documents sharing a tag, the doc↔doc form is O(N²) edges saying one thing; the
tag-node form is N, and a traversal still connects any two of them in two hops.

Everything is emitted sorted and de-duplicated, so the `edges` table is
byte-reproducible like the rest of the substrate.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import PurePosixPath

EXTRACTED = "EXTRACTED"
INFERRED = "INFERRED"

TOP_TERMS = 24  # per doc (handoff open question 3; tuned on eval at M8)

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_CITATION_HEADING_RE = re.compile(r"^#{1,6}\s*(citations?|references|sources)\s*$", re.I)

# Terms that describe every document say nothing about any of them.
_STOPWORDS = frozenset(
    """a an and are as at be but by for from has have how i if in into is it its
    of on or that the their then there these this to was were what when where
    which who why will with you your we our not can may""".split()
)


@dataclass(frozen=True, order=True)
class Edge:
    src: str
    kind: str
    dst: str
    grade: str = EXTRACTED

    def as_row(self) -> tuple[str, str, str, str]:
        return (self.src, self.kind, self.dst, self.grade)


def scan_document(body: str, meta: dict, entry: dict) -> dict:
    """Everything the graph needs from one document, read once at conversion time.

    Deliberately split from :func:`edges_from_scans`: *reading* a document is
    the expensive half and is per-document, so it is cached in the index and
    skipped for unchanged files. *Resolving* links needs the whole corpus (a
    new document can make an existing dangling link resolve), so it is cheap,
    in-memory, and re-run every ingest.
    """
    return {
        "outline": _outline(body),
        "top_terms": " ".join(_top_terms(body)),
        "links": [[target, cited] for target, cited in _links(body)],
        "tags": _tags(meta),
        "parent": entry.get("parent", ""),
        "url": entry.get("url", ""),
    }


def edges_from_scans(scans: dict[str, dict]) -> list[Edge]:
    """All edges for a corpus, from per-document scans.

    Link targets only become edges when they resolve to a document actually in
    the corpus — a dangling link is a fact about the source, not a
    relationship, and minting a node for it would put unreachable ids in the
    graph.
    """
    known = set(scans)
    urls = {s["url"]: doc_id for doc_id, s in scans.items() if s.get("url")}
    edges: set[Edge] = set()
    for doc_id in sorted(scans):
        scan = scans[doc_id]
        for target, in_citations in scan.get("links", []):
            dst = _resolve(doc_id, target, known, urls)
            if dst is not None and dst != doc_id:  # self-links carry no information
                edges.add(Edge(doc_id, "cites" if in_citations else "references", dst))
        parent = scan.get("parent")
        if parent and parent in urls:
            edges.add(Edge(doc_id, "crawled_from", urls[parent]))
        for tag in scan.get("tags", []):
            edges.add(Edge(doc_id, "tagged", f"tag:{tag}"))
    return sorted(edges)


# -- internals -------------------------------------------------------------


def _links(body: str) -> list[tuple[str, bool]]:
    """Every markdown link, flagged by whether it sits under a citations heading."""
    sections = _citation_spans(body)
    out = []
    for match in _LINK_RE.finditer(body):
        in_citations = any(start <= match.start() < end for start, end in sections)
        out.append((match.group(1), in_citations))
    return out


def _citation_spans(body: str) -> list[tuple[int, int]]:
    """Character ranges covered by a Citations/References section."""
    spans = []
    headings = list(_HEADING_RE.finditer(body))
    for i, match in enumerate(headings):
        if not _CITATION_HEADING_RE.match(match.group(0).strip()):
            continue
        level = len(match.group(1))
        end = len(body)
        for later in headings[i + 1 :]:  # the section ends at the next peer or higher
            if len(later.group(1)) <= level:
                end = later.start()
                break
        spans.append((match.end(), end))
    return spans


def _resolve(doc_id: str, target: str, known: set[str], urls: dict[str, str]) -> str | None:
    target = target.split("#", 1)[0].strip()
    if not target:
        return None  # pure anchor: same document
    if target in urls:
        return urls[target]  # an external link we happen to have crawled
    if target.startswith(("http://", "https://", "mailto:", "tel:")):
        return None
    if target.startswith("/"):
        candidate = target.lstrip("/")
    else:
        base = PurePosixPath(doc_id).parent
        candidate = str(PurePosixPath(base) / target) if str(base) != "." else target
    candidate = _normalize(candidate)
    if candidate in known:
        return candidate
    # a link to a directory conventionally means its index
    for suffix in ("/index.md", "/README.md"):
        if _normalize(candidate + suffix) in known:
            return _normalize(candidate + suffix)
    return None


def _normalize(path: str) -> str:
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


def _tags(meta: dict) -> list[str]:
    raw = meta.get("tags")
    if isinstance(raw, str):
        raw = [t.strip() for t in raw.split(",")]
    if not isinstance(raw, list):
        return []
    return sorted({str(t).strip().lower() for t in raw if str(t).strip()})


def _outline(body: str) -> str:
    headings = [m.group(2) for m in _HEADING_RE.finditer(body)]
    return " › ".join(headings[:12])


def _top_terms(body: str, limit: int = TOP_TERMS) -> list[str]:
    from ..index.bm25f import tokenize

    counts = Counter(
        term for term in tokenize(body) if term not in _STOPWORDS and len(term) > 2
    )
    # (-count, term): frequency first, then alphabetical — never insertion order
    return [term for term, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]]
