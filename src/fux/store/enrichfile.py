"""The enrichment file's format — `.fux/enrich/<sha>.md`, read side.

Core layer (W-282): `fux enrich` and `fux correct` (the writer) write these
files, `fux ingest` folds them into the index, and the ranker (the reader)
reads their provenance, so the path, the frontmatter and the validity test
live here and neither side imports the other. Planning, the self-retrieval
check and the verb stay in `enrich.py`
([SR-ENRICH](../../../records/0137_enrich.md)).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..constants import fixed

ENRICH_DIR = fixed("files", "enrich_dir")

#: Keys fux VERIFIES versus keys it merely RECORDS.
#:
#: `source_sha` is computed and checked — a mismatch means stale, full stop.
#: `model` is a **claim**: an agent is asked to stamp what produced the text,
#: and nothing here can confirm it. That asymmetry is the honest cost of
#: Arpit's ruling and the record says so rather than implying provenance is
#: proven.
REQUIRED_KEYS = ("source", "source_sha", "chunks", "model", "generated", "skill")

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def enrich_path(root: Path, sha: str) -> Path:
    return root / ENRICH_DIR / f"{sha}.md"


def parse_frontmatter(text: str) -> dict | None:
    """A permissive `key: value` read of the leading block, or `None`.

    Deliberately not a YAML parser: the block is written by an agent following
    a skill, the key set is closed and flat, and adopting a parser to read six
    strings would be the same L2 trade this whole design refuses.
    """
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        return None
    out: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def validate(path: Path, expected_sha: str | None = None) -> str | None:
    """`None` when the file is a usable enrichment, else why it is not."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"unreadable: {exc}"
    meta = parse_frontmatter(text)
    if meta is None:
        return "no frontmatter block"
    missing = [k for k in REQUIRED_KEYS if not meta.get(k)]
    if missing:
        return f"frontmatter missing {', '.join(missing)}"
    if expected_sha is not None and meta.get("source_sha") != expected_sha:
        return f"source_sha {meta.get('source_sha')!r} does not match the document"
    if not text[match_end(text):].strip():
        return "no body after the frontmatter"
    return None


def is_question(line: str) -> bool:
    """Is this body line a question a searcher would type?

    Deliberately shallow: a line ending in `?`. **The skill asks for one
    question per line**, and a cleverer test — leading interrogative, a parser —
    would refuse lines a human wrote on purpose and pass lines it should not.
    Prose bodies written under the older skill contain no `?`-terminated lines
    as a rule, and they stay valid either way (`plan()` only checks what looks
    like a question).
    """
    stripped = line.strip().lstrip("-*").strip()
    return stripped.endswith("?") and len(stripped) > 1


def superseded_by(text: str) -> str:
    """The `superseded_by:` value in an enrichment's frontmatter, or `""`.

    **The declared path a retired document cannot state about itself.** A
    document's own `supersedes:` is written by the *successor*; a document that
    was retired years ago cannot name a successor that did not exist. An
    enrichment file is written later, so it can — and this is the only key in
    that frontmatter that reaches the ranking rather than a report.

    ⚠ **Declared, never inferred**, exactly as `ingest/priors.py::superseded_ids`
    is: nothing here guesses from titles, numbering or dates.
    """
    meta = parse_frontmatter(text)
    return (meta or {}).get("superseded_by", "").strip()


def match_end(text: str) -> int:
    match = _FRONTMATTER_RE.match(text)
    return match.end() if match else 0
