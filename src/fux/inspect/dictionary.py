"""The local hash -> word dictionary: `.fux/runtime/inspect/dictionary.json`.

## The constraint that shapes this whole file

The committed index holds **term hashes, not words** — 8-byte blake2b keys,
a deliberate privacy property ([SR-POSTINGS](../../../records/0112_postings.md)
decision 2). So *"the word `tldr` is on every document"* cannot be read off the
index at all, and the one honest way to get it is to **re-tokenise the sources
locally with the same analyzer** and join the result to the index's statistics.

⚠ **The text is REDACTED first, with the repository's own `pii.toml` rules, and
that is not a nicety.** Without it this file would be built from raw bytes while
the index was built from redacted ones, and two things would go wrong at once: a
value `pii.toml` exists to remove — a card number, an employee id — would be
**named in a report**, and the hashes would not even be the index's, because
`[PII:name]` is what ingest actually hashed. The redaction phase is imported
from `ingest/run.py`'s own module rather than re-implemented, and applied to the
body and to the frontmatter title, which is the third source of committed
vocabulary and the one that was missed once already.

Three further properties make this safe rather than a hole in L2:

- **The dictionary is gitignored.** It lands under `.fux/runtime/`, which is
  DERIVED — rebuildable, disposable, and already ignored by the `.gitignore`
  `fux setup` writes. Nothing new is committed, so the privacy property the
  hashes buy is unchanged for everyone who clones the repo.
- **It holds terms, not text.** A term is a statistic; a line of a document is
  content. Nothing here retains a sentence, a position, or an order — only the
  set of analyzed words and how a human spells each one.
- **It never fetches.** A `url:` document is read from `.fux/acquired/` if its
  bytes were retained and is skipped otherwise (L4). A `file:` document is read
  out of the working tree, which is not a fetch.

## Why the surface spelling is here at all

An analyzed term is not a word anyone typed: `mTLS` analyzes to `mtl`, and a
report saying *"`mtl` is on 40 % of your documents"* sends the reader looking
for a typo. `analyze_pairs` hands back `(surface, analyzed)` for the same
tokens, so this stores both — the analyzed term as the key's meaning and the
**most frequent surface spelling** as what the report prints.

⚠ **The field texts are built by `ingest/extract.py`'s own helpers, imported
rather than reimplemented.** A heading is a heading because `_headings_and_body`
says so (it knows about code fences, and about `.rst`/`.adoc`/`.org`), and a
title is `_title`'s answer. A second copy of that logic here would name words
the index does not hold and miss words it does, and the report would be
confidently wrong about which terms exist.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from ..store import fuxdir

__all__ = ["Dictionary", "INSPECT_DIR", "DICTIONARY_NAME", "build", "load_or_build", "inspect_dir"]

INSPECT_DIR = "inspect"
DICTIONARY_NAME = "dictionary.json"
SCHEMA = "fux.inspect.dictionary.v1"


@dataclass
class Dictionary:
    """hash -> (analyzed term, surface spelling), plus what could not be read.

    `unreadable` and `undecodable` are separated because they are different
    findings with different levers: bytes that are not there (a `url:` document
    with nothing retained, a file deleted since ingest) versus bytes a decoder
    could not turn into text — which is the *analyzer coverage* lens's subject
    and a `fux-decoder` job.
    """

    terms: dict[str, str] = field(default_factory=dict)
    surfaces: dict[str, str] = field(default_factory=dict)
    #: doc id -> why no words came out of it
    unreadable: dict[str, str] = field(default_factory=dict)
    undecodable: list[str] = field(default_factory=list)
    #: doc id -> (raw word-like runs in the source, analyzed tokens kept)
    token_counts: dict[str, tuple[int, int]] = field(default_factory=dict)
    shards: dict[str, str] = field(default_factory=dict)

    def name(self, term_hash: str) -> str:
        """The word to print for a hash, or the hash itself when unknown.

        **Never a blank and never a guess.** An unnamed term is a real state —
        the document it came from is not readable from here — and printing the
        hash says so without pretending the term does not exist.
        """
        return self.surfaces.get(term_hash) or self.terms.get(term_hash) or term_hash

    def coverage(self, term_hashes) -> tuple[int, int]:
        """`(named, total)` over the term hashes given."""
        total = 0
        named = 0
        for h in term_hashes:
            total += 1
            if h in self.terms:
                named += 1
        return named, total


def inspect_dir(root: Path) -> Path:
    """`.fux/runtime/inspect/`, created. Gitignored by `runtime/`'s own line."""
    directory = fuxdir.derived_dir(root, "runtime") / INSPECT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _dictionary_path(root: Path) -> Path:
    return inspect_dir(root) / DICTIONARY_NAME


def build(root: Path, view, *, progress=None) -> Dictionary:
    """Re-tokenise every document in `view` and return the dictionary.

    Deterministic: documents are visited in `view.docs` order (sorted by id),
    and a surface tie is broken by the spelling itself, so the same sources
    produce the same file twice.
    """
    from ..ingest import pii as pii_mod
    from ..ingest.extract import _headings_and_body, _title
    from ..ingest.parse import parse_document
    from ..progress import NULL as _NULL_PROGRESS
    from ..query.tokenize import tokenize_pairs
    from ..store import term_hash

    progress = progress or _NULL_PROGRESS
    # The repository's own rules. `load` never raises for an absent file -- the
    # CLI gate refuses the verb long before this -- and an empty ruleset
    # redacts nothing, which is the common case.
    try:
        pii_rules = pii_mod.load(root)
    except Exception:  # pragma: no cover - a report must not fail a command
        pii_rules = ()
    out = Dictionary(shards=dict(view.shards))
    counters: dict[str, Counter] = {}

    with progress.phase("dictionary", len(view.docs), "docs") as p:
        for doc in view.docs:
            p.update(1)
            raw = _source_bytes(root, doc)
            if raw is None:
                out.unreadable[doc.id] = _why_unreadable(root, doc)
                continue
            parsed = parse_document(raw, doc.loc, root)
            if parsed is None:
                out.undecodable.append(doc.id)
                out.unreadable[doc.id] = "no text came out of it (a decoder owns the type and got nothing)"
                continue
            # ⚠ **Redact BEFORE splitting headings off the body**, in the same
            # order `ingest/run.py` does: its redact phase runs over `parsed`
            # and `_headings_and_body` cuts the headings out afterwards. Doing
            # it the other way round leaves a heading unredacted, and a heading
            # is indexed vocabulary.
            body, meta = parsed.body, parsed.meta
            if pii_rules:
                body, _hits = pii_mod.redact(pii_rules, body)
                front = meta.get("title")
                if isinstance(front, str) and front:
                    redacted_title, title_hits = pii_mod.redact(pii_rules, front)
                    if title_hits:
                        meta = {**meta, "title": redacted_title}
            headings, stripped = _headings_and_body(doc.loc, body)
            title = _title(meta, headings, doc.loc)
            # The same five texts `extract_fields` tokenises, in the same order.
            # Concatenating them is safe HERE and nowhere else: a term's
            # per-field tf matters to ranking and not to naming, and the union
            # of the five fields' terms is exactly the record's `terms` keys.
            texts = (
                stripped,
                " ".join(headings),
                title,
                doc.loc.replace("/", " ").replace(".", " "),
                _enrichment(root, doc.sha, pii_rules),
            )
            raw_runs = 0
            kept = 0
            for text in texts:
                if not text:
                    continue
                raw_runs += _word_runs(text)
                for surface, analyzed in tokenize_pairs(text):
                    kept += 1
                    h = term_hash(analyzed)
                    out.terms[h] = analyzed
                    counters.setdefault(h, Counter())[surface] += 1
            out.token_counts[doc.id] = (raw_runs, kept)

    for h, counter in counters.items():
        # Most frequent spelling; ties broken by the spelling itself so the
        # file is a function of the sources and not of iteration order.
        out.surfaces[h] = min(counter.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return out


def _word_runs(text: str) -> int:
    """How many word-like runs the analyzer SAW, before stopwords and splitting.

    The denominator of the *analyzer coverage* lens: `kept / saw` says how much
    of the document's text became searchable vocabulary. Counted with the
    analyzer's own `_WORD_RE` so the two numbers are about the same thing.
    """
    from ..query.analyzer import _WORD_RE

    return sum(1 for _ in _WORD_RE.finditer(text))


def _source_bytes(root: Path, doc) -> bytes | None:
    """This document's source bytes, from disk only. Never a fetch (L4)."""
    if doc.id.startswith("url:"):
        from ..refer import source as refer_source

        fetched = refer_source.from_acquired(root, doc.id, doc.loc)
        return fetched.content if fetched is not None else None
    path = root / doc.loc
    try:
        if not path.is_file():
            return None
        return path.read_bytes()
    except OSError:
        return None


def _why_unreadable(root: Path, doc) -> str:
    if doc.id.startswith("url:"):
        return "a url: document with no retained bytes in .fux/acquired/ (keep = true retains them; inspect never fetches)"
    return "not in the working tree at the indexed loc"


def _enrichment(root: Path, sha: str, pii_rules=()) -> str:
    """The pinned enrichment BODY for a source sha, redacted, or `""`.

    Frontmatter-stripped and validated, exactly as `ingest/run.py` reads it —
    the frontmatter is provenance and is not indexed, so naming its words here
    would attribute terms to a document the index never gave them to.

    ⚠ **Redacted for the same reason the body is**, and it is the surface that
    leaked once: W-102 found enrichment reaching `.fux/index/` unredacted
    because the redact phase walks document bodies and this text never enters
    that map. It does not enter this function's caller's map either.
    """
    if not sha:
        return ""
    from ..enrich import enrich_path, match_end, validate

    path = enrich_path(root, sha)
    if not path.is_file() or validate(path, expected_sha=sha) is not None:
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    body = text[match_end(text):]
    if pii_rules:
        body, _hits = pii_mod_redact(pii_rules, body)
    return body


def pii_mod_redact(rules, text: str):
    """`ingest.pii.redact`, imported at call time.

    Named here rather than imported at module scope for the reason every import
    in this file is deferred: `fux --version` must stay instant, and
    `fux.ingest` pulls the decoders in behind it.
    """
    from ..ingest import pii as pii_mod

    return pii_mod.redact(rules, text)


def save(root: Path, dictionary: Dictionary) -> Path:
    path = _dictionary_path(root)
    payload = {
        "schema": SCHEMA,
        "shards": dictionary.shards,
        "terms": {h: [dictionary.terms[h], dictionary.surfaces.get(h, "")] for h in sorted(dictionary.terms)},
        "unreadable": dict(sorted(dictionary.unreadable.items())),
        "undecodable": sorted(dictionary.undecodable),
        "token_counts": {k: list(v) for k, v in sorted(dictionary.token_counts.items())},
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load(root: Path, view) -> Dictionary | None:
    """The cached dictionary, or `None` when it is absent or stale.

    Staleness is the **shard content shas**, not an mtime: the dictionary
    describes the vocabulary behind a particular index, and an index that
    changed by one document names one more word. An mtime would report a
    `git checkout` as fresh.
    """
    path = _dictionary_path(root)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if payload.get("schema") != SCHEMA or payload.get("shards") != view.shards:
        return None
    out = Dictionary(shards=payload.get("shards", {}))
    for h, pair in payload.get("terms", {}).items():
        analyzed, surface = (pair + ["", ""])[:2] if isinstance(pair, list) else (pair, "")
        out.terms[h] = analyzed
        if surface:
            out.surfaces[h] = surface
    out.unreadable = dict(payload.get("unreadable", {}))
    out.undecodable = list(payload.get("undecodable", []))
    out.token_counts = {k: tuple(v) for k, v in payload.get("token_counts", {}).items()}
    return out


def load_or_build(root: Path, view, *, rebuild: bool = False, progress=None) -> Dictionary:
    if not rebuild:
        cached = load(root, view)
        if cached is not None:
            return cached
    dictionary = build(root, view, progress=progress)
    save(root, dictionary)
    return dictionary
