"""Git-dir source adapter — the committed directory list, and a sorted walk of it.

The list is `.fux/sources/dirs` (ADR-DIR-LIST), read through the one shared
grammar in `sourcelist.py`: one entry per line, `#` comments, the loader
dedupes and sorts, and a line may declare `archived=true`.

Each entry is a directory (walked recursively) or a single file, relative to
the repo root. Reads raw bytes directly off the filesystem (no git plumbing —
"git-dir" names the fact that these are files living in a git checkout, not a
dependency on git object hashes). Binary, non-UTF8, and empty files are
skipped with a reason, never a crash; a configured source that doesn't exist
on disk is a misconfiguration and fails loudly instead.

**`archived` is parsed, and since 2026-08-22 it is read.** The declaration is
the half this module owns. `archived_dirs()` exposes it and `is_archived_loc()`
is the one test for whether a `loc` falls under one — used by `ingest/run.py` to
stamp the record property (ADR-ARCHIVED-CONTENT decision 1) and by
`query/rank.py` for the marker and the demotion. **One definition, because two
copies of this predicate is a differential-law failure waiting for them to
drift.** The ranking is still byte-identical at the default weight — which is
ADR-ARCHIVED-CONTENT decision 2, and it has a test.

## `.fuxignore` is consulted first, and everything else is a conjunction

**One file outranks the rest**: `.fux/.fuxignore`
([ADR-FUXIGNORE](../../../docs/adr/0047_fuxignore.md)), a `.gitignore`-shaped
list where `!` **re-includes**. Its verdict is taken before anything else and
it decides in both directions — an ignored path is skipped whatever the rest
says, and an explicitly `!`-re-included path skips straight past the exclusions
and the type allowlist.

**Below it, the remaining conditions are still a conjunction with no
precedence.** A path `.fuxignore` says nothing about is indexed **iff** all
three hold:

1. it lives under an **included** `dirs` entry;
2. no `!` **exclusion** entry matches it or any of its ancestors
   (ADR-DIR-LIST, W-45's verdict E) — the **deprecated** home for exclusions,
   still honoured, and `fux ingest` warns when a pattern is stated here *and*
   in `.fuxignore`;
3. its name matches the **type allowlist** — `.fux/sources/types` if that file
   exists, otherwise the built-in `DEFAULT_TYPES` (ADR-TYPES, W-55's verdict G).

**No rule inside that trio beats another**, so there is nothing to remember
about precedence among them and nothing to get wrong. Every file that fails one
of them — or that `.fuxignore` ignored — is reported as *skipped with a reason*
rather than silently dropped, and `.fuxignore`'s reason names the file, the
line number and the pattern. An invisible filter is the failure mode every one
of these items was opened about.

## A skip carries its CLASS, and the two are counted separately

Every `Skipped` says whether it is `POLICY` — a line somebody wrote — or
`UNREADABLE` — fux looked and found nothing to index. **The class is set at the
point of the skip, never re-derived from the reason string**, so renaming a
reason cannot silently move a file between the two counts.

Why it exists: on the fux repo itself an ingest reported `599 skipped`, of which
**598 were the type allowlist doing exactly its job** and one was a file worth
looking at. One number over two populations is a number nobody reads — the same
failure `skipnotice` was written for, arrived at from the other side. See
ADR-INGEST decision 15.

**The content skips are not overridable and are not meant to be.** `empty`,
`binary` and `non-utf8` apply to a `!`-re-included file exactly as they do to
any other: there is nothing for a decoder or an analyzer to read either way, so
a switch that turned them off would only move the emptiness one layer down.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .. import decode as decode_mod
from ..config import DEFAULT_TYPES_FILE as TYPES_FILE
from ..errors import FuxError
from . import fuxignore, sourcelist


@dataclass(frozen=True)
class WalkedFile:
    rel_path: str  # posix, relative to root
    content: bytes


#: The two reasons a path is not in the index, and **they are different news.**
#:
#: - `POLICY` — a committed list said not to index it: `.fux/.fuxignore`, a
#:   `!` exclusion in `.fux/sources/dirs`, or the type allowlist. Nothing is
#:   wrong. Somebody wrote a line and fux obeyed it.
#: - `UNREADABLE` — fux looked and there was nothing to index: an empty file,
#:   bytes no decoder claims, a fetch that failed.
#:
#: Collapsing the two into one count is what made `599 skipped` unreadable on
#: a real corpus: 598 of them were the type allowlist doing its job and one was
#: a file that should have been there. See ADR-INGEST decision 15.
POLICY = "policy"
UNREADABLE = "unreadable"

#: The bytes never arrived — a 404, a timeout, a refused connection. **Only ever
#: set on the URL path**, where retrieval can fail independently of whether the
#: document would have been readable.
#:
#: ⚠ **The distinction that earns a third value: a model cannot fix a 404.**
#: `UNREADABLE` means fux held the bytes and got nothing out of them, which is
#: exactly what `.fux/enrich/queue.tsv` is for. `UNFETCHED` means there were no
#: bytes, so queueing it would put a work item in front of a person that no
#: amount of enrichment discharges — and the queue is committed, so it would be
#: a work item in front of the whole team.
#:
#: Set at the skip site like the other two, never re-derived from `reason`.
UNFETCHED = "unfetched"


@dataclass(frozen=True)
class Skipped:
    rel_path: str
    reason: str
    #: `POLICY` or `UNREADABLE`, **set where the skip is made** — never
    #: re-derived by reading `reason` back, which would put the classification
    #: one string edit away from being silently wrong.
    #:
    #: ⚠ **The default is `UNREADABLE` on purpose.** A call site nobody updated
    #: over-reports into the loud bucket, where a person investigates and finds
    #: nothing wrong. The other default would hide a real problem inside the
    #: deliberate count, and nothing would ever surface it.
    kind: str = UNREADABLE

    @property
    def deliberate(self) -> bool:
        """True when a line somebody wrote is the whole explanation."""
        return self.kind == POLICY


def would_index(root: Path, rel: str, *, excludes, types: TypeFilter | None) -> bool:
    """Would this path be indexed if the `.fuxignore` blocks were not there?

    **The staleness test for a fux-written line.** A generated line freezes the
    verdict that produced it, which is the accepted cost of keeping the list in
    a committed file — but a frozen verdict that has since become *wrong* is an
    invisible filter, and an invisible filter is the failure every one of these
    items was opened about. This is what makes it visible.

    The three conditions in the same order the walk applies them, so the answer
    cannot drift from the walk's. **Bytes are read only for a path that already
    passed both lists**, which is why this costs nothing on the population that
    is large: a `.py` file fails the allowlist and is never opened.
    """
    path = root / rel
    if not path.is_file():
        return False
    if _excluded_by(rel, list(excludes or [])) is not None:
        return False
    if types is not None and not types.accepts(rel):
        return False
    try:
        return _skip_reason(path.read_bytes(), rel, root) is None
    except OSError:
        return False


def _generated_kind(verdict: fuxignore.Verdict) -> str:
    """The class a `.fuxignore` ignore asserts.

    A hand-written line is always `POLICY` — somebody wrote it. A generated
    line's class is **the block it is in**, which is why the writer keeps two
    blocks rather than one: the class is stated by position and never parsed
    out of the note.
    """
    if verdict.generated is None:
        return POLICY
    return POLICY if verdict.generated.block == fuxignore.BLOCK_NOT_INDEXED else UNREADABLE


def partition(skips: list[Skipped]) -> tuple[list[Skipped], list[Skipped]]:
    """`(not_indexed, unreadable)` — the deliberate skips and the rest.

    Order is preserved in both halves, so a caller that was handed a sorted
    list gets two sorted lists and never has to re-sort (L3: `walk_sources`
    and `fetch_all` both sort, and the printer depends on it).
    """
    return [s for s in skips if s.deliberate], [s for s in skips if not s.deliberate]


def read_dirs(root: Path, rel_path: str) -> list[sourcelist.Entry]:
    """Parse the committed directory list through the one shared grammar.

    Deduped and sorted by entry, so file order is presentation only — a human
    may group by team or by system and it cannot change a committed byte.
    """
    return sourcelist.read(
        root,
        rel_path,
        sourcelist.DIRS,
        missing_hint=(
            "create it with one directory or file per line (a line may carry "
            "`archived=true`), or run `fux setup` to write a starter"
        ),
    )


def source_dirs(root: Path, rel_path: str) -> list[str]:
    """Just the **included** entry values. Exclusions are `source_excludes`."""
    return [entry.value for entry in read_dirs(root, rel_path) if not entry.exclude]


def source_excludes(root: Path, rel_path: str) -> list[str]:
    """The `!` patterns — repo-relative globs, applied to the whole walk."""
    return [entry.value for entry in read_dirs(root, rel_path) if entry.exclude]


def archived_dirs(root: Path, rel_path: str) -> list[str]:
    """Included entries declared `archived=true` (ADR-ARCHIVED-CONTENT decision 6's
    input). Reads the same committed declaration ADR-ARCHIVED-CONTENT decision 1 leaves off the
    record — the ranking keys off the source list, never a path convention
    (ADR-DIR-LIST decision 4)."""
    return [
        entry.value
        for entry in read_dirs(root, rel_path)
        if not entry.exclude and entry.attrs.get("archived") == "true"
    ]


def enrich_dirs(root: Path, rel_path: str) -> list[str]:
    """Included entries declared `enrich=true` (W-76 Phase 8).

    The same shape as `archived_dirs` and read from the same committed file,
    because the two answer the same kind of question: *which directories did a
    human decide something about?* Neither is ever inferred from a path.
    """
    return [
        entry.value
        for entry in read_dirs(root, rel_path)
        if not entry.exclude and entry.attrs.get("enrich") == "true"
    ]


def is_archived_loc(loc: str, archived_dirs) -> bool:
    """`loc` falls under one of `archived_dirs` — a directory entry or an exact
    single-file entry, mirroring how `walk_sources` resolves an entry against
    the filesystem.

    **The one definition.** `ingest/run.py` stamps the record property with it
    and `query/rank.py` reads it for the marker and the demotion; a second copy
    would let the property and the marker disagree about the same document.
    """
    return any(loc == d or loc.startswith(f"{d}/") for d in archived_dirs)


#: What counts as a document when the consumer has not said otherwise.
#: **Prose formats only.** No `.json`, `.svg`, `.sh`, `.py` or `.mermaid`: they
#: are machine data or diagram source, and indexing them was the W-55 defect.
#: No extensionless files either — those are `LICENSE`, `Makefile` and
#: `Dockerfile` far more often than they are documents.
#: Prose formats that need no decoder — already text, walked since the
#: allowlist shipped.
_PROSE_TYPES: tuple[str, ...] = ("*.md", "*.markdown", "*.txt", "*.rst", "*.adoc", "*.org")


def _default_types() -> tuple[str, ...]:
    """The built-in allowlist: prose, plus everything a built-in decoder reads.

    ⚠ **Widened 2026-08-26 on Arpit's ruling** — *"all the ones which have a
    decoder"*. [ADR-TYPES](../../../docs/adr/0031_types-list.md) verdict G had
    kept the default to six prose globs, on a measurement showing 14 % of this
    repo's documents were non-prose and carried 15 % of its tokens, `.json`
    alone at 11.4 %. **That measurement stands and was not overturned**; what
    changed is that those tokens were *raw bytes* — the file WAS the body,
    UUIDs and base64 included. Every one of them now passes through a decoder
    that emits keys as headings and drops ids, hashes, timestamps and numbers.
    Verdict G's own confidence line called the default's contents *"a defaults
    judgment rather than a measurement"*, which is why a ruling could move it.

    ⚠ **Derived from BUILT-IN decoders only, never from the live registry.** A
    default that grew when a consumer dropped a `logdoc.py` into
    `.fux/decoders/` would mean **adding a decoder silently starts indexing a
    new file type** — and what counts as a document must stay a committed line
    a human wrote in `.fux/sources/types`.
    """
    from .. import decode as decode_mod

    return tuple(sorted({*_PROSE_TYPES, *(f"*{e}" for e in decode_mod.builtin_extensions())}))


DEFAULT_TYPES: tuple[str, ...] = _default_types()


@dataclass(frozen=True)
class TypeFilter:
    """Which filenames are documents. `allow` is never empty by construction."""

    allow: tuple[str, ...]
    deny: tuple[str, ...] = ()
    #: True when the built-in default is in force — i.e. no types file exists.
    default: bool = True

    def accepts(self, rel_path: str) -> bool:
        if any(sourcelist.glob_match(p, rel_path) for p in self.deny):
            return False
        return any(sourcelist.glob_match(p, rel_path) for p in self.allow)


def read_types(root: Path, rel_path: str = TYPES_FILE) -> TypeFilter:
    """The type allowlist: the committed file if present, else the built-in.

    **Absent means the default applies, never "index everything".** Indexing
    everything is the behaviour W-55 was filed about; and it does not mean
    "index nothing" either, because a missing config that empties the index
    looks like a broken engine rather than a missing file.
    """
    path = root / rel_path
    if not path.is_file():
        return TypeFilter(allow=DEFAULT_TYPES)

    entries = sourcelist.parse(path.read_text(encoding="utf-8"), sourcelist.TYPES, origin=str(path))
    allow = tuple(e.value for e in entries if not e.exclude)
    deny = tuple(e.value for e in entries if e.exclude)
    if not allow:
        raise FuxError(
            f"{path}: lists no file types, so nothing would be indexed. Delete the file to take "
            f"the built-in default ({', '.join(DEFAULT_TYPES)}), or add at least one pattern"
        )
    return TypeFilter(allow=allow, deny=deny, default=False)


def walk_sources(
    root: Path,
    dirs: list[str],
    *,
    excludes: list[str] | None = None,
    types: TypeFilter | None = None,
    ignores: fuxignore.Ignores | None = None,
) -> tuple[list[WalkedFile], list[Skipped]]:
    """Walk the included roots, subtract the exclusions, keep only document types.

    `excludes`, `types` and `ignores` default to "nothing excluded, everything
    allowed, no opinions" so a caller that has not been updated keeps its old
    behaviour — but **no such caller ships**: `ingest` passes all three, and the
    defaults exist for tests that are exercising one condition at a time.

    **`ignores` is checked first and can end the question in either
    direction** (ADR-FUXIGNORE decision 4). An empty `Ignores` — which is what
    a repo with no `.fuxignore` produces — is indistinguishable from not
    passing one, so the old two-condition behaviour is exactly what a repo that
    has not adopted the file still gets.
    """
    excludes = excludes or []
    ignores = ignores if ignores is not None else fuxignore.Ignores()
    files: dict[str, bytes] = {}
    #: rel -> (reason, kind). The kind is decided at the point of the skip.
    skipped: dict[str, tuple[str, str]] = {}
    for entry in dirs:
        base = root / entry
        if not base.exists():
            raise FuxError(f"configured source not found: {entry!r} (looked in {base})")
        for path in _candidate_paths(base):
            # NFC, the same normalization `parse.py` applies to file content
            # (the R1/macOS-checkout hazard): a filesystem may return a path
            # in NFD even when the file was created and committed as NFC, so
            # the same document's `rel_path`/`loc` would differ by checkout
            # machine without this — a byte-identical-index guarantee (L3)
            # that a path string, not just content, has to hold too.
            rel = unicodedata.normalize("NFC", path.relative_to(root).as_posix())
            if rel in files or rel in skipped:
                continue  # already covered by an earlier, overlapping entry

            # `.fuxignore` first, and its answer is final in BOTH directions.
            # An explicit `!` re-include is the one thing that outranks the
            # type allowlist, which is why `reincluded` is a distinct state
            # from "no rule matched" rather than a bool for "not ignored".
            verdict = ignores.decide(rel)
            if verdict.ignored:
                # A fux-written block line carries BOTH halves forward: its
                # note is the reason that put it there, and which block it
                # sits in is its class. Neither is re-derived, so a second run
                # reports exactly what the first one found rather than
                # *"because .fuxignore says so"*.
                skipped[rel] = (verdict.reason(), _generated_kind(verdict))
                continue
            if not verdict.reincluded:
                pattern = _excluded_by(rel, excludes)
                if pattern is not None:
                    skipped[rel] = (f"excluded by !{pattern}", POLICY)
                    continue
                if types is not None and not types.accepts(rel):
                    skipped[rel] = ("not an indexed file type", POLICY)
                    continue

            # Past this line nothing a human wrote is in play any more: the
            # bytes themselves decide, so every skip below is UNREADABLE.
            content = path.read_bytes()
            reason = _skip_reason(content, rel, root)
            if reason:
                skipped[rel] = (reason, UNREADABLE)
            else:
                files[rel] = content

    walked = sorted((WalkedFile(rel, content) for rel, content in files.items()), key=lambda f: f.rel_path)
    skips = sorted(
        (Skipped(rel, reason, kind) for rel, (reason, kind) in skipped.items()),
        key=lambda s: s.rel_path,
    )
    return walked, skips


def _excluded_by(rel: str, excludes: list[str]) -> str | None:
    """The first pattern that removes this path, or `None`.

    A pattern matches the file **or any ancestor directory**, so
    `!work/regression/*/evidence` removes the directory and everything under
    it — which is what a reader of that line expects, and the only reading
    under which excluding a tree is one line rather than one line per file.
    """
    parts = rel.split("/")
    ancestors = ["/".join(parts[: i + 1]) for i in range(len(parts))]
    for pattern in excludes:
        if any(sourcelist.glob_match(pattern, candidate) for candidate in ancestors):
            return pattern
    return None


def _candidate_paths(base: Path):
    if base.is_file():
        yield base
        return
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(base).parts):
            continue  # dotfiles/dotdirs (.git, .DS_Store, …) are never doc content
        yield path


def _skip_reason(content: bytes, rel: str = "", root: Path | None = None) -> str | None:
    """Why this file is not a document, or `None`.

    ⚠ **"binary" and "non-utf8" stopped being sufficient reasons the moment
    decoders existed** (W-86). A `.docx` is a zip, a `.pdf` is compressed
    streams — both contain NUL bytes and neither decodes as UTF-8, and both are
    documents. So a claimed extension is checked *before* the byte tests, and
    only unclaimed files are still judged on their bytes.

    Empty stays a skip regardless: there is nothing for any decoder to read.
    """
    if not content:
        return "empty"
    if rel and decode_mod.claims(rel, root):
        return None  # a decoder owns this type; its bytes are its own business
    if b"\x00" in content:
        return "binary"
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return "non-utf8"
    return None
