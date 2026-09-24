"""Pass A — the per-document facts: decode → fields → analyze → chunk.

**W-220's first rung** ([SR-INSPECT](../../../records/0156_inspect.md) decision
17). One summary per document, computed with **the engine's own helpers,
imported** (decision 5): `decode.decode` and `ingest.parse.parse_document` for
what came out of the bytes, `ingest.extract._headings_and_body` for the
fields, `refer._chunk.chunk` for the passages refer would cite. A second
copy of any of them would describe a document the engine never built.

## The cache, and why its key has five parts

`.fux/runtime/inspect/facts.json` — gitignored, like everything under
`runtime/`. One entry per document, keyed on everything that can change a
summary:

| part | what moves it |
|---|---|
| the source `sha` | the document changed |
| the decoder digest | `decoderdigest.of` — a built-in's `VERSION`, a consumer file's bytes |
| `extract.RULES_VERSION` | the field rules changed, corpus-wide |
| `store.format.ANALYZER_VERSION` | the analyzer changed |
| the `[refer]` passage bounds | a different chunk |

**An unchanged document is never recomputed**, and a decoder bump recomputes
only the documents that decoder reads — the digest is per extension, exactly as
ingest's reuse key is (SR-INGEST, W-166).

⚠ **The summary holds counts, never text.** A heading is counted, not kept; a
passage is a size and a cut rung. Words a person reads come from the per-document
X-ray (`xray.document`), computed on demand and never cached.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "DATA_SUFFIXES",
    "FACTS_NAME",
    "Facts",
    "compute",
    "is_data",
    "load_or_compute",
    "load_or_compute_one",
    "readable_text",
]

FACTS_NAME = "facts.json"
SCHEMA = "fux.inspect.facts.v1"

#: The data formats Arpit ruled are held to BOTH bars — identifiable and
#: reachable (W-220, 2026-09-23). Everything else is prose.
DATA_SUFFIXES = (".json", ".jsonl", ".csv", ".toml", ".yaml", ".yml")

#: HTML elements that are page furniture rather than the page. Counting what
#: the engine's OWN decoder keeps of them is the finding; this list only names
#: what to take out for the comparison, and removes nothing from any index.
_CHROME = re.compile(rb"<(nav|header|aside|footer)\b[^>]*>.*?</\1\s*>", re.I | re.S)

#: An inline Markdown link's target: `[text](target)`. Its words are tokenised
#: into `body` today (W-220 finding 5).
_LINK_TARGET = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def is_data(loc: str) -> bool:
    lowered = loc.lower()
    return any(lowered.endswith(suffix) for suffix in DATA_SUFFIXES)


@dataclass
class Facts:
    """Every document's summary, by id, plus how many were computed this run.

    `computed` and `cached` are **not** part of any report — a first run and a
    second run over the same index must print the same bytes (SR-INSPECT
    decision 14) — they exist so a test can prove the cache was used.
    """

    by_id: dict[str, dict] = field(default_factory=dict)
    computed: int = 0
    cached: int = 0


def _suffix(loc: str) -> str:
    name = loc.rsplit("/", 1)[-1]
    return "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""


def cache_key(sha: str, decoder_digest: str, bounds: tuple[int, int]) -> str:
    from ..ingest.extract import RULES_VERSION
    from ..store.format import ANALYZER_VERSION

    return f"{sha}|{decoder_digest}|rules{RULES_VERSION}|{ANALYZER_VERSION}|refer{bounds[0]}-{bounds[1]}"


def refer_bounds(root: Path) -> tuple[int, int]:
    from .. import tune as tune_mod

    try:
        tune = tune_mod.load(root)
    except Exception:  # pragma: no cover - a report must not fail on a bad tune
        return 120, 4000
    return tune.min_passage_bytes, tune.max_passage_bytes


def source_bytes(root: Path, doc_id: str, loc: str) -> bytes | None:
    """This document's bytes from disk, never a fetch (L4) — `dictionary`'s rule."""
    from .dictionary import _source_bytes

    class _D:  # the two attributes `_source_bytes` reads
        pass

    d = _D()
    d.id, d.loc = doc_id, loc
    return _source_bytes(root, d)


def readable_text(root: Path, doc_id: str, loc: str, raw: bytes) -> tuple[str, bool]:
    """The text refer chunks, and whether a decoder produced it.

    The same choice `refer._readable` makes: a `file:` document is decoded when a
    decoder claims it, and read as UTF-8 otherwise; a `url:` document's retained
    bytes are already what was indexed.
    """
    if doc_id.startswith("url:"):
        return raw.decode("utf-8", errors="replace"), False
    from ..decode import DecodeFailed, decode

    try:
        decoded = decode(raw, loc, root)
    except DecodeFailed:
        decoded = None
    if decoded is None:
        return raw.decode("utf-8", errors="replace"), False
    return decoded, True


def compute(root: Path, doc, *, decoder: str, bounds: tuple[int, int]) -> dict:
    """One document's summary. **Never raises** — a report must not fail on one file."""
    from ..ingest.extract import _headings_and_body
    from ..ingest.parse import parse_document
    from ..query.tokenize import tokenize
    from ..refer._chunk import chunk

    out: dict = {
        "decoder": decoder,
        "kind": "data" if is_data(doc.loc) else "prose",
        "readable": False,
        "source_bytes": None,
        "text_bytes": 0,
        "decoded": False,
        "title_source": "",
        "headings": 0,
        "body_tokens": 0,
        "link_target_tokens": 0,
        "chrome_tokens": 0,
        "passages": 0,
        "cuts": {"author": 0, "line": 0, "word": 0},
        "passage_bytes": {},
    }
    raw = source_bytes(root, doc.id, doc.loc)
    if raw is None:
        return out
    out["readable"] = True
    out["source_bytes"] = len(raw)
    try:
        parsed = parse_document(raw, doc.loc, root)
    except Exception:  # pragma: no cover - DecodeFailed is already a None
        parsed = None
    if parsed is not None:
        headings, stripped = _headings_and_body(doc.loc, parsed.body)
        front = parsed.meta.get("title")
        out["title_source"] = (
            "front-matter" if isinstance(front, str) and front.strip()
            else "heading" if headings
            else "file name"
        )
        out["headings"] = len(headings)
        out["body_tokens"] = len(tokenize(stripped))
        out["link_target_tokens"] = sum(
            len(tokenize(m.group(1).replace("/", " ").replace(".", " ")))
            for m in _LINK_TARGET.finditer(stripped)
        )
    if _suffix(doc.loc) in (".html", ".htm") and not doc.id.startswith("url:"):
        out["chrome_tokens"] = _chrome_tokens(root, doc.loc, raw)
    try:
        text, generated = readable_text(root, doc.id, doc.loc, raw)
    except Exception:  # pragma: no cover
        text, generated = "", False
    out["decoded"] = generated
    out["text_bytes"] = len(text.encode("utf-8"))
    passages = chunk(text, min_passage_bytes=bounds[0], max_passage_bytes=bounds[1]) if text else []
    out["passages"] = len(passages)
    for p in passages:
        out["cuts"][p.cut or "author"] = out["cuts"].get(p.cut or "author", 0) + 1
    sizes = sorted(p.nbytes for p in passages)
    if sizes:
        out["passage_bytes"] = {"min": sizes[0], "p50": sizes[len(sizes) // 2], "max": sizes[-1]}
    return out


def _chrome_tokens(root: Path, loc: str, raw: bytes) -> int:
    """Tokens the engine's own html decoder KEEPS from `nav`/`header`/`aside`/`footer`.

    Decoded twice — as it is, and with those elements removed — and the
    difference in analyzed tokens is the chrome that reached the index. Measured
    through the decoder rather than on the raw markup, so a decoder that already
    skips an element counts it as zero, which is the truth.
    """
    from ..decode import DecodeFailed, decode
    from ..query.tokenize import tokenize

    stripped = _CHROME.sub(b"", raw)
    if stripped == raw:
        return 0
    try:
        whole = decode(raw, loc, root) or ""
        bare = decode(stripped, loc, root) or ""
    except DecodeFailed:
        return 0
    return max(0, len(tokenize(whole)) - len(tokenize(bare)))


def _path(root: Path) -> Path:
    from .dictionary import inspect_dir

    return inspect_dir(root) / FACTS_NAME


def _decoders(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """`(extension -> digest, loc -> decoder name)` — the register names the decoder."""
    from ..ingest import decoderdigest, register

    digests = decoderdigest.binding_digests(root)
    names = {loc: row.decoder.split("@", 1)[0] for loc, row in register.read(root).items()}
    return digests, names


def _read_cache(root: Path) -> dict:
    try:
        payload = json.loads(_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload.get("facts", {}) if payload.get("schema") == SCHEMA else {}


def _write_cache(root: Path, facts: dict) -> None:
    try:
        _path(root).write_text(
            json.dumps({"schema": SCHEMA, "facts": dict(sorted(facts.items()))}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError:  # pragma: no cover - a cache that cannot be written is a slower next run
        pass


def _key_and_decoder(doc, digests, names, bounds) -> tuple[str, str]:
    suffix = _suffix(doc.loc)
    digest = digests.get(suffix, "prose")
    decoder = names.get(doc.loc) or (digest.split("@", 1)[0] if suffix in digests else "prose")
    return cache_key(doc.sha, digest, bounds), decoder


def load_or_compute_one(root: Path, view, doc) -> dict:
    """ONE document's facts through the same cache — what a click in `fux serve` runs.

    The other entries are left exactly as they were: a click never recomputes,
    or drops, another document's facts.
    """
    cached = _read_cache(root)
    digests, names = _decoders(root)
    key, decoder = _key_and_decoder(doc, digests, names, refer_bounds(root))
    hit = cached.get(doc.id)
    if hit is not None and hit.get("key") == key:
        return hit
    entry = {"key": key, **compute(root, doc, decoder=decoder, bounds=refer_bounds(root))}
    cached[doc.id] = entry
    _write_cache(root, cached)
    return entry


def load_or_compute(root: Path, view, *, progress=None) -> Facts:
    """Every document's facts, reusing each cached entry whose key still matches."""
    from ..progress import NULL as _NULL_PROGRESS

    progress = progress or _NULL_PROGRESS
    cached = _read_cache(root)
    bounds = refer_bounds(root)
    digests, names = _decoders(root)
    out = Facts()
    fresh: dict[str, dict] = {}
    with progress.phase("facts", len(view.docs), "docs") as p:
        for doc in view.docs:
            p.update(1)
            key, decoder = _key_and_decoder(doc, digests, names, bounds)
            hit = cached.get(doc.id)
            if hit is not None and hit.get("key") == key:
                entry = hit
                out.cached += 1
            else:
                entry = {"key": key, **compute(root, doc, decoder=decoder, bounds=bounds)}
                out.computed += 1
            fresh[doc.id] = entry
    out.by_id = fresh
    if out.computed or set(cached) != set(fresh):
        _write_cache(root, fresh)
    return out
