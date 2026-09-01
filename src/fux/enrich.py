"""`fux enrich` — the deterministic halves. W-76 Phase 8.

**Fux does not call a model.** Arpit's ruling, 2026-08-23:

> *"Enrich should work like a skill in the chat — that way we don't need to
> integrate the API in the code and AI coding agents can be used."*

This is [ADR-FETCHER](../../docs/adr/0019_fetcher.md)'s pattern applied to a
second boundary. Network I/O is something fux refuses to own, so it lives in
consumer code under `.fux/fetchers/`; model calls are the same, so they live in
an agent skill the consumer invokes. **Fux says what needs doing and validates
what came back.** Nothing here imports an SDK, opens a socket, or holds a key —
so **L1 and L4 are held, not bracketed**, and the `$0` law survives.

That leaves two deterministic halves, and they are what this module is:

- `fux enrich --plan`  — compute the worklist: which documents in a declared
  scope are missing enrichment or have stale enrichment, and where it goes.
- `fux enrich --check` — validate what exists and report coverage.

**There is no `--model` flag**, because there is no networked path to fence.

## Why the sha keying matters more than it looks

Enrichment is keyed by the source document's content sha. Edit a document and
its enrichment no longer matches — so it is ignored, automatically, with no
staleness check to forget to write. **The corollary is that partial coverage is
the steady state, not a degraded mode**: one commit after a full pass and you
are at 408/411. Any design that only works at 100 % coverage is broken on day
two, which is why scope is declared per source line rather than assumed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .errors import FuxError

ENRICH_DIR = ".fux/enrich"

#: Keys fux VERIFIES versus keys it merely RECORDS.
#:
#: `source_sha` is computed and checked — a mismatch means stale, full stop.
#: `model` is a **claim**: an agent is asked to stamp what produced the text,
#: and nothing here can confirm it. That asymmetry is the honest cost of
#: Arpit's ruling and the record says so rather than implying provenance is
#: proven.
REQUIRED_KEYS = ("source", "source_sha", "chunks", "model", "generated", "skill")

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


@dataclass(frozen=True)
class PlanItem:
    loc: str
    sha: str
    chunks: int
    state: str  # "missing" | "stale"
    target: str
    stale_sha: str = ""


@dataclass(frozen=True)
class ScopeReport:
    scope: str
    total: int
    ok: int
    missing: list[PlanItem]
    stale: list[PlanItem]
    malformed: list[tuple[str, str]]

    @property
    def covered(self) -> int:
        return self.ok


def enrich_path(root: Path, sha: str) -> Path:
    return root / ENRICH_DIR / f"{sha}.md"


def parse_frontmatter(text: str) -> dict | None:
    """A permissive `key: value` read of the leading block, or `None`.

    Deliberately not a YAML parser: the block is written by an agent following
    a skill, the key set is closed and flat, and adopting a parser to read six
    strings would be the same L1 trade this whole design refuses.
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


def match_end(text: str) -> int:
    match = _FRONTMATTER_RE.match(text)
    return match.end() if match else 0


def plan(root: Path, scopes: dict[str, list[dict]]) -> list[ScopeReport]:
    """The worklist, per declared scope.

    `scopes` maps a scope prefix to the records under it. Only scopes a source
    line declared `enrich=true` are passed in — **partial coverage across the
    corpus is intended and declared**; partial coverage *inside* a scope is the
    defect this reports.
    """
    reports: list[ScopeReport] = []
    for scope in sorted(scopes):
        records = scopes[scope]
        missing: list[PlanItem] = []
        stale: list[PlanItem] = []
        malformed: list[tuple[str, str]] = []
        ok = 0
        for record in sorted(records, key=lambda r: r["loc"]):
            sha = record.get("sha", "")
            chunks = _chunk_count(root, record)
            target = f"{ENRICH_DIR}/{sha}.md"
            path = enrich_path(root, sha)
            if not path.is_file():
                # A sha with no file is MISSING. It is also what a stale
                # enrichment looks like from this side: the old file is still
                # on disk under the OLD sha, orphaned rather than wrong.
                prior = _orphan_for(root, record)
                if prior:
                    stale.append(
                        PlanItem(record["loc"], sha, chunks, "stale", target, stale_sha=prior)
                    )
                else:
                    missing.append(PlanItem(record["loc"], sha, chunks, "missing", target))
                continue
            problem = validate(path, expected_sha=sha)
            if problem:
                malformed.append((str(path.relative_to(root)), problem))
            else:
                ok += 1
        reports.append(ScopeReport(scope, len(records), ok, missing, stale, malformed))
    return reports


def _chunk_count(root: Path, record: dict) -> int:
    """How many passages this document splits into — the unit of enrichment.

    Computed from the document rather than stored: it is a pure function of
    bytes fux already has, and storing it would be a committed field that
    changes whenever the chunker is tuned.
    """
    from .refer._chunk import chunk

    text = _document_text(root, record)
    if text is None:
        return 0
    return len(chunk(text))


#: The synthetic scope every enrichable `url:` document falls under.
#:
#: A `dirs` scope is a path prefix, which is a real grouping a human chose. A
#: URL list has no such structure -- the lines share nothing but being URLs --
#: so inventing per-host scopes would report coverage against a grouping
#: nobody declared. One scope, named after the file the declaration lives in.
URL_SCOPE = ".fux/sources/urls"


def _document_text(root: Path, record: dict) -> str | None:
    """The document's own text, for a `file:` or a `url:` record alike.

    ⚠ **A `url:` document is readable here only because `.fux/acquired/`
    exists.** Before the acquired plane, planning enrichment for a URL would
    have meant a network fetch inside `fux enrich --plan` -- an offline,
    read-only command (L4) -- so the attribute could not exist on that list at
    all. `keep=true` is the default, so this works without configuration; a
    line that opted out with `keep=false` has nothing to read and reports zero
    chunks, which `--plan` names rather than hiding.
    """
    loc = record.get("loc", "")
    if record.get("src") == "url":
        from .ingest.urlsrc import _decode_fetched
        from .store import acquired

        blob = acquired.read_manifest(root).get(loc)
        path = acquired.stored(root, loc)
        if blob is None or path is None:
            return None
        try:
            markdown, _why = _decode_fetched(path.read_bytes(), blob.content_type, loc, root)
        except Exception:
            # A blob that no longer decodes is "we cannot count this", never a
            # crash inside a planning command.
            return None
        return markdown

    path = root / loc
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _orphan_for(root: Path, record: dict) -> str:
    """An enrichment file that names this document but a different sha.

    Distinguishes "never enriched" from "enriched, then the document changed",
    which are the same absence on disk and very different to a reader deciding
    whether the corpus is half-finished or merely edited.
    """
    directory = root / ENRICH_DIR
    if not directory.is_dir():
        return ""
    loc = record.get("loc")
    for candidate in sorted(directory.glob("*.md")):
        meta = parse_frontmatter(candidate.read_text(encoding="utf-8", errors="replace"))
        if meta and meta.get("source") == loc:
            return candidate.stem
    return ""


def prune(root: Path, live_shas: set[str]) -> list[Path]:
    """Enrichment files no document currently hashes to.

    **Never automatic.** A reverted document recovers its enrichment for free
    because the old sha comes back and the file is still there — deleting
    orphans on sight would throw that away for a saving measured in kilobytes.
    """
    directory = root / ENRICH_DIR
    if not directory.is_dir():
        return []
    return [p for p in sorted(directory.glob("*.md")) if p.stem not in live_shas]


def cmd_enrich(args) -> int:
    from .config import find_root

    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run from inside a configured repo")

    scopes = _scopes(root)
    if not scopes:
        print(
            "no enrichment scopes declared.\n"
            "Add `enrich=true` to a directory line in .fux/sources/dirs, e.g.:\n"
            "    docs/adr              enrich=true"
        )
        return 0

    reports = plan(root, scopes)
    if getattr(args, "check", False):
        return _render_check(reports)
    return _render_plan(root, reports)


def _scopes(root: Path) -> dict[str, list[dict]]:
    from . import store as store_mod
    from .ingest.gitdir import enrich_dirs

    declared = enrich_dirs(root, ".fux/sources/dirs")
    urls = _enrich_urls(root)
    if not declared and not urls:
        return {}
    out: dict[str, list[dict]] = {scope: [] for scope in declared}
    if urls:
        out[URL_SCOPE] = []
    for record in store_mod.read_index(root).values():
        loc = record.get("loc", "")
        if record.get("src") == "url":
            # A URL is IN the scope or it is not -- there is no prefix
            # question, because the declaration names the URL exactly.
            if loc in urls:
                out[URL_SCOPE].append(record)
            continue
        for scope in declared:
            if loc == scope or loc.startswith(scope.rstrip("/") + "/"):
                out[scope].append(record)
                break
    return {scope: records for scope, records in out.items() if scope in declared or records}


def _enrich_urls(root: Path) -> set[str]:
    """URLs whose line says `enrich=true`, resolved through the three layers.

    Absent or unreadable list is an empty set, never an error: `fux enrich` is
    a planning command over whatever is declared, and a repo with no URL source
    has simply declared nothing.
    """
    from .config import load as load_config
    from .ingest import urlsrc

    try:
        source = load_config(root).url
        if source is None:
            return set()
        entries = urlsrc.read_urls(root, source.urls_file)
    except FuxError:
        return set()
    # The same three layers every URL attribute uses: built-in default, then
    # `[sources.url] enrich`, then the line. A line that DECLARED it wins.
    out: set[str] = set()
    for entry in entries:
        if "enrich" in entry.declared:
            on = entry.attrs["enrich"] == "true"
        else:
            on = getattr(source, "enrich", False)
        if on:
            out.add(entry.value)
    return out


def _render_plan(root: Path, reports: list[ScopeReport]) -> int:
    total_docs = total_chunks = 0
    for report in reports:
        work = report.missing + report.stale
        print(f"scope {report.scope} (enrich=true)")
        if not work:
            print(f"  {report.ok}/{report.total} ok — nothing to do")
        for item in work:
            # **The FULL sha, never a prefix.** The skill instructs the agent
            # to copy this value into `source_sha:` and to name the file after
            # it, and `validate()` compares it against the record's full sha.
            # Printing 12 characters here made every enrichment written by
            # following the skill come back STALE -- and the message rendered
            # as `STALE (was c84a92145ee9)` directly under `sha c84a92145ee9`,
            # so the one line that exists to show a difference showed two
            # identical strings. Found 2026-08-24 by running the skill.
            marker = "MISSING" if item.state == "missing" else f"STALE (was {item.stale_sha})"
            print(f"  {item.loc}  sha {item.sha}  {item.chunks} chunks  {marker}")
            total_docs += 1
            total_chunks += item.chunks
    if total_docs:
        print(f"\n-> {total_docs} documents, {total_chunks} chunks")
        print(f"   write each to {ENRICH_DIR}/<sha>.md")
        print("   invoke the `fux-enrich` skill in your coding agent to generate them")
    return 0


def _render_check(reports: list[ScopeReport]) -> int:
    bad = 0
    print(f"enrichment: {len(reports)} scope(s) declared")
    for report in reports:
        bits = []
        if report.stale:
            bits.append(f"{len(report.stale)} stale")
        if report.missing:
            bits.append(f"{len(report.missing)} missing")
        if report.malformed:
            bits.append(f"{len(report.malformed)} malformed")
            bad += len(report.malformed)
        suffix = "  " + " · ".join(bits) if bits else "  ok"
        print(f"  {report.scope:<28} {report.ok}/{report.total}{suffix}")
        for path, why in report.malformed:
            print(f"      refused: {path} — {why}")
    if any(r.missing or r.stale for r in reports):
        print("\nrun `fux enrich --plan`, then the `fux-enrich` skill")
    return 1 if bad else 0
