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
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from .parse import ParsedDoc

EXTRACTED_GRADE = 10
AMBIG_GRADE = 8
INFERRED_GRADE = 6

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")


@dataclass(frozen=True)
class DocScan:
    links: list[str]
    code_spans: list[str]
    tags: list[str]


def scan(doc: ParsedDoc) -> DocScan:
    return DocScan(
        links=[m.group(1) for m in _LINK_RE.finditer(doc.body)],
        code_spans=[m.group(1) for m in _INLINE_CODE_RE.finditer(doc.body)],
        tags=_scan_tags(doc.meta),
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


def resolve(doc_id: str, doc_scan: DocScan, known_ids: set[str], by_basename: dict[str, list[str]]) -> list[dict]:
    edges: dict[tuple[str, str], int] = {}

    for target in doc_scan.links:
        dst = _resolve_ref(doc_id, target, known_ids)
        if dst and dst != doc_id:
            edges[("ref", dst)] = EXTRACTED_GRADE

    for tag in doc_scan.tags:
        edges[("tag", f"tag:{tag}")] = EXTRACTED_GRADE

    for span in doc_scan.code_spans:
        resolved = _resolve_code(span, known_ids, by_basename)
        if resolved and resolved[0] != doc_id:
            dst, grade = resolved
            edges[("code", dst)] = max(grade, edges.get(("code", dst), 0))

    return [{"kind": kind, "dst": dst, "grade": grade} for (kind, dst), grade in sorted(edges.items())]


def _resolve_ref(doc_id: str, target: str, known_ids: set[str]) -> str | None:
    target = target.split("#", 1)[0].strip()
    if not target or target.startswith(("http://", "https://", "mailto:", "tel:")):
        return None
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


def _scan_tags(meta: dict) -> list[str]:
    raw = meta.get("tags")
    if isinstance(raw, str):
        raw = [t.strip() for t in raw.split(",")]
    if not isinstance(raw, list):
        return []
    return sorted({str(t).strip().lower() for t in raw if str(t).strip()})
