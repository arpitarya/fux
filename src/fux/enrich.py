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

## The enrichment plane is inside the redaction boundary — W-102

An enrichment body is committed **and** indexed, so a value written into one
travels twice: in the file every clone gets, and as a term in `.fux/index/`.
ADR-PII decision 1 covers both, and until W-102 neither was checked —
`run.py`'s redact phase walks document bodies, and the enrichment text never
entered that map.

Two halves, in two places, and they are deliberately different:

- **`run.py` redacts** the body before it becomes `ctx`, so the committed index
  is clean whether or not anybody runs this command.
- **`--check` refuses and never rewrites.** The file is prose a human reviews
  in a diff; rewriting it silently would make that diff lie. And redaction is
  not the remedy here anyway — a redacted enrichment body indexes
  `[PII:email]` as vocabulary. The fix is to write the sentence differently.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
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
    #: W-102. `(path, [rule names])` for every enrichment whose BODY matches a
    #: `.fux/pii.toml` rule. Separate from `malformed` because the remedy is
    #: different: a malformed file is fixed by adding a key, this one is fixed
    #: by rewriting the prose, and conflating them would offer the wrong advice.
    pii: list[tuple[str, list[str]]] = field(default_factory=list)
    #: Documents in this scope that fell outside a `TARGET` selector. Reported
    #: so a filtered run can never read as a scope being complete (W-104).
    filtered: int = 0

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


def plan(
    root: Path,
    scopes: dict[str, list[dict]],
    *,
    target: str | None = None,
    pii_rules: tuple = (),
) -> list[ScopeReport]:
    """The worklist, per declared scope.

    `scopes` maps a scope prefix to the records under it. Only scopes a source
    line declared `enrich=true` are passed in — **partial coverage across the
    corpus is intended and declared**; partial coverage *inside* a scope is the
    defect this reports.

    ## `target` filters; it never widens — W-104

    🔴 **A selector narrows the report and changes nothing about scope.** A
    document no `enrich=true` line reaches is not in `scopes` at all, so naming
    it here cannot make it enrichable. Which directories get enriched stays a
    human's declaration (ADR-ENRICH decision 4), and this parameter is one step
    away from being the thing that quietly overrides it. Matching is **exact**
    — not a prefix and not a glob — because a selector that silently matches
    two documents turns a one-document request into a bulk run.

    `total` still counts the whole scope and `filtered` counts what the
    selector excluded, so a single-target run cannot be read as `n/n`.
    """
    reports: list[ScopeReport] = []
    for scope in sorted(scopes):
        records = scopes[scope]
        missing: list[PlanItem] = []
        stale: list[PlanItem] = []
        malformed: list[tuple[str, str]] = []
        pii_found: list[tuple[str, list[str]]] = []
        ok = 0
        filtered = 0
        for record in sorted(records, key=lambda r: r["loc"]):
            if target is not None and record.get("loc") != target:
                filtered += 1
                continue
            sha = record.get("sha", "")
            chunks = _chunk_count(root, record)
            enrich_target = f"{ENRICH_DIR}/{sha}.md"
            path = enrich_path(root, sha)
            if not path.is_file():
                # A sha with no file is MISSING. It is also what a stale
                # enrichment looks like from this side: the old file is still
                # on disk under the OLD sha, orphaned rather than wrong.
                prior = _orphan_for(root, record)
                if prior:
                    stale.append(
                        PlanItem(record["loc"], sha, chunks, "stale", enrich_target,
                                 stale_sha=prior)
                    )
                else:
                    missing.append(
                        PlanItem(record["loc"], sha, chunks, "missing", enrich_target)
                    )
                continue
            problem = validate(path, expected_sha=sha)
            if problem:
                malformed.append((_shown(path, root), problem))
                continue
            # W-102. A well-formed enrichment can still carry a value that must
            # not be committed. Checked AFTER `validate` so one file never
            # reports two faults, and only on files that would actually be
            # indexed -- a malformed file's text reaches nothing.
            fired = _pii_in_body(path, pii_rules)
            if fired:
                pii_found.append((_shown(path, root), fired))
                continue
            ok += 1
        reports.append(
            ScopeReport(scope, len(records), ok, missing, stale, malformed,
                        pii=pii_found, filtered=filtered)
        )
    return reports


def _shown(path: Path, root: Path) -> str:
    """An enrichment file's path as this command spells it, on every platform.

    ⚠ **`str(Path)` is `\\` on Windows, and this report already had a `/`
    spelling.** `plan()`'s worklist names each file as
    `.fux/enrich/<sha>.md` (built from `ENRICH_DIR`, a literal), while its
    `malformed:` and `refused:` lines came from `str(path.relative_to(root))`
    — so one Windows run printed **the same file two different ways**, and a
    consumer grepping their own log for a path found half of it.

    Fux spells a `loc` with forward slashes everywhere else; this is that,
    applied to the one report that had drifted. It is display only — nothing
    opens a file by this string.
    """
    return path.relative_to(root).as_posix()


def _pii_in_body(path: Path, rules: tuple) -> list[str]:
    """Rule names that fire on this enrichment's BODY, in file order.

    ⚠ **The body only.** The frontmatter is provenance — `model:`, `generated:`
    — it is stripped before indexing (ADR-ENRICH decision 8), so nothing in it
    reaches a committed term, and refusing a file over a value the index never
    sees would be a false positive with no remedy.

    ⚠ **This reports; it never rewrites.** `fux enrich --check` is a validator
    and the file is prose a human reviews in a diff — the same discipline as
    `fux doctor` reporting a lock it will not clear (ADR-MAINTENANCE veto 7),
    and stronger here, because a silent rewrite would make that diff lie.

    Nor is redacting the file the fix a consumer should reach for: a redacted
    body indexes `[PII:email]` as vocabulary, which is worse than useless. The
    remedy is to rewrite the sentence without the value.
    """
    if not rules:
        return []
    from .ingest import pii as pii_mod

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    _redacted, hits = pii_mod.redact(rules, text[match_end(text):])
    return [name for name in hits]


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
    from .ingest import pii as pii_mod

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

    target = getattr(args, "target", None)
    if target is not None:
        problem = _target_problem(root, scopes, target)
        if problem:
            print(problem)
            return 1

    # Loaded ONCE, here, and a malformed ruleset stops the command rather than
    # surfacing per file -- the same argument `fetch_all` makes for
    # `refusals.load`. A repo whose `pii.toml` cannot be read is a repo whose
    # redaction is off, and finding that out per-file is finding it out late.
    pii_rules = pii_mod.load(root)

    reports = plan(root, scopes, target=target, pii_rules=pii_rules)
    if getattr(args, "check", False):
        return _render_check(reports, target=target)
    return _render_plan(root, reports, target=target)


def _target_problem(root: Path, scopes: dict[str, list[dict]], target: str) -> str:
    """Why this `TARGET` cannot be planned, or `""` when it can.

    🔴 **Two failures that look identical and are fixed differently**, which is
    the whole reason this function exists rather than one "not found" line:

    - **not declared** — fux has the document, but no `enrich=true` line reaches
      it. The fix is a human's edit to `.fux/sources/dirs` or the URL list, and
      it is deliberately not something this command will do for them
      (ADR-ENRICH decision 4).
    - **not indexed** — fux has never seen it. The fix is `fux ingest`, or a
      path that is spelled the way the index spells it.
    """
    for records in scopes.values():
        for record in records:
            if record.get("loc") == target:
                return ""
    from . import store as store_mod

    try:
        known = {r.get("loc") for r in store_mod.read_index(root).values()}
    except Exception:  # an unreadable index is not this command's error to name
        known = set()
    if target in known:
        return (
            f"{target} is indexed but no enrichment scope reaches it.\n"
            "Add `enrich=true` to the directory line that covers it in "
            ".fux/sources/dirs, or to its line in the URL list.\n"
            "Naming a document here does not enrich it -- which directories are "
            "enriched is your declaration, not this command's."
        )
    return (
        f"{target} is not in the index, so there is nothing to plan for it.\n"
        "Run `fux ingest` first, and use the loc exactly as `fux find` prints "
        "it -- matching here is exact, never a prefix."
    )


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


def _render_plan(root: Path, reports: list[ScopeReport], *, target: str | None = None) -> int:
    total_docs = total_chunks = 0
    for report in reports:
        work = report.missing + report.stale
        if target is not None and not work and not report.filtered:
            continue
        suffix = f" — filtered to {target}" if target is not None else ""
        print(f"scope {report.scope} (enrich=true){suffix}")
        if not work:
            # ⚠ `report.total` is the WHOLE scope, deliberately, even under a
            # selector: a one-document run must never render as `n/n`, which is
            # the sentence the skill reads to decide a scope is finished.
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
        if target is None and total_docs > 1:
            # W-104. The skill asks before a bulk run; saying so here means a
            # human reading the plan directly gets the same offer, and means the
            # skill's prompt is not the only place the choice is visible.
            print("   one document at a time: fux enrich --plan <loc-or-url>")
    return 0


def _render_check(reports: list[ScopeReport], *, target: str | None = None) -> int:
    bad = 0
    scope_word = "scope(s) declared" if target is None else f"scope(s), filtered to {target}"
    print(f"enrichment: {len(reports)} {scope_word}")
    for report in reports:
        bits = []
        if report.stale:
            bits.append(f"{len(report.stale)} stale")
        if report.missing:
            bits.append(f"{len(report.missing)} missing")
        if report.malformed:
            bits.append(f"{len(report.malformed)} malformed")
            bad += len(report.malformed)
        if report.pii:
            bits.append(f"{len(report.pii)} carrying PII")
            bad += len(report.pii)
        suffix = "  " + " · ".join(bits) if bits else "  ok"
        print(f"  {report.scope:<28} {report.ok}/{report.total}{suffix}")
        for path, why in report.malformed:
            print(f"      refused: {path} — {why}")
        for path, names in report.pii:
            # ADR-PII decision 7's reasoning applied to a second surface: say
            # WHICH rule fired. `[REDACTED]` everywhere destroys that, and so
            # does "this file contains PII".
            print(f"      refused: {path} — matches .fux/pii.toml rule(s): {', '.join(names)}")
    if any(r.pii for r in reports):
        print(
            "\nAn enrichment body is committed AND indexed, so a value in one travels "
            "twice over.\n"
            "Rewrite the sentence without the value. Do NOT add a pii.toml rule to "
            "cover it:\n"
            "a redacted enrichment body indexes `[PII:email]` as vocabulary, which is "
            "worse than useless."
        )
    if any(r.missing or r.stale for r in reports):
        print("\nrun `fux enrich --plan`, then the `fux-enrich` skill")
    return 1 if bad else 0
