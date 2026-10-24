"""Git-dir source adapter — a sorted walk of the listed paths.

The list is the `paths:` half of `.fux/sources.yaml` (SR-SOURCES), read by
`sourcesfile.py`: the loader sorts, and a path under `archived:` is declared
archived.

Each entry is a directory (walked recursively) or a single file, relative to
the repo root. Reads raw bytes directly off the filesystem (no git plumbing —
"git-dir" names the fact that these are files living in a git checkout, not a
dependency on git object hashes). Binary, non-UTF8, and empty files are
skipped with a reason, never a crash; a configured source that doesn't exist
on disk is a misconfiguration and fails loudly instead.

**`archived` is parsed, and since 2026-08-22 it is read.** The declaration is
the half this module owns. `sourcesfile.archived_paths()` exposes it and `is_archived_loc()`
is the one test for whether a `loc` falls under one — used by `ingest/run.py` to
stamp the record property (SR-ARCHIVED-CONTENT decision 1) and by
`query/rank.py` for the marker and the demotion. **One definition, because two
copies of this predicate is a differential-law failure waiting for them to
drift.** The ranking is still byte-identical at the default weight — which is
SR-ARCHIVED-CONTENT decision 2, and it has a test.

## `.fuxignore` is consulted first, and everything else is a conjunction

**One file outranks the rest**: `.fux/.fuxignore`
([SR-FUXIGNORE](../../../records/0144_fuxignore.md)), a `.gitignore`-shaped
list where `!` **re-includes**. Its verdict is taken before anything else and
it decides in both directions — an ignored path is skipped whatever the rest
says, and an explicitly `!`-re-included path skips straight past the exclusions
and the type allowlist.

**Below it, the remaining conditions are still a conjunction with no
precedence.** A path `.fuxignore` says nothing about is indexed **iff** all
three hold:

1. it lives under a **listed** path;
2. its name matches the **type allowlist** — `.fux/config/formats.toml` if that file
   exists, otherwise the built-in `DEFAULT_TYPES` (SR-TYPES, W-55's verdict G).

**There is no third condition any more** (W-294): the `!` lines `.fux/sources/dirs`
carried were the second home for exclusion, with the opposite meaning of `!` in
`.fuxignore`, and they moved into `.fuxignore` when the list became
`.fux/sources.yaml`.

🔴 **A directory a hand-written `.fuxignore` pattern ignores is PRUNED, never
entered** (W-244's rule, carried to the file that now holds every exclusion).
Git's rule — a file under an ignored directory cannot be re-included — is what
makes the prune exact rather than an approximation: `Ignores.decide` says no
file beneath it can come back. On this repository that is the L11 guard: the
walk never lists `work/golden/`.

**No rule inside that pair beats another**, so there is nothing to remember
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
SR-INGEST decision 15.

**The content skips are not overridable and are not meant to be.** `empty`,
`binary` and `non-utf8` apply to a `!`-re-included file exactly as they do to
any other: there is nothing for a decoder or an analyzer to read either way, so
a switch that turned them off would only move the emptiness one layer down.
"""

from __future__ import annotations

import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .. import decode as decode_mod
from ..config import DEFAULT_TYPES_FILE as TYPES_FILE
from ..errors import FuxError
from . import fuxignore, sourcelist
from ..constants import fixed


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
#: a file that should have been there. See SR-INGEST decision 15.
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


def would_index(root: Path, rel: str, *, types: TypeFilter | None) -> bool:
    """Would this path be indexed if the `.fuxignore` blocks were not there?

    **The staleness test for a fux-written line.** A generated line freezes the
    verdict that produced it, which is the accepted cost of keeping the list in
    a committed file — but a frozen verdict that has since become *wrong* is an
    invisible filter, and an invisible filter is the failure every one of these
    items was opened about. This is what makes it visible.

    The conditions in the same order the walk applies them, so the answer
    cannot drift from the walk's. **Bytes are read only for a path that already
    passed the allowlist**, which is why this costs nothing on the population that
    is large: a `.py` file fails the allowlist and is never opened.
    """
    path = root / rel
    if not path.is_file():
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
    list gets two sorted lists and never has to re-sort (L4: `walk_sources`
    and `fetch_all` both sort, and the printer depends on it).
    """
    return [s for s in skips if s.deliberate], [s for s in skips if not s.deliberate]


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
_PROSE_TYPES: tuple[str, ...] = tuple(fixed("decoders", "prose_types"))


def _default_types() -> tuple[str, ...]:
    """The built-in allowlist: prose, plus everything a built-in decoder reads.

    ⚠ **Widened 2026-08-26 on Arpit's ruling** — *"all the ones which have a
    decoder"*. [SR-TYPES](../../../records/0128_types-list.md) verdict G had
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
    a human wrote in `.fux/config/formats.toml`.
    """
    from .. import decode as decode_mod

    return tuple(sorted({*_PROSE_TYPES, *(f"*{e}" for e in decode_mod.builtin_extensions())}))


DEFAULT_TYPES: tuple[str, ...] = _default_types()


@dataclass(frozen=True)
class TypeFilter:
    """Which filenames are documents. `allow` is never empty by construction.

    ⚠ **There is no `deny` any more** (SR-TYPES decision 12, 2026-09-11). The
    `!` subtraction the old line grammar carried was already the deprecated
    spelling of an exclusion; `.fux/config/formats.toml` has no such key, and
    `.fux/.fuxignore` is the one home for keeping a file out.
    """

    allow: tuple[str, ...]
    #: True when the built-in default is in force — i.e. no types file exists.
    default: bool = True
    #: W-289: the globs `.fux/config/formats.toml` admits that no declared package can
    #: read (`readable()`). A file one of them matches is not walked and is NOT
    #: a skip — it is counted on `fux ingest`'s stderr instead (SR-PLUGINS P5).
    undeclared: tuple[str, ...] = ()

    def accepts(self, rel_path: str) -> bool:
        return any(sourcelist.glob_match(p, rel_path) for p in self.allow)

    def awaits_package(self, rel_path: str) -> bool:
        """Is this file out only because its format's package is undeclared?"""
        return any(sourcelist.glob_match(p, rel_path) for p in self.undeclared)


def read_types(root: Path, rel_path: str = TYPES_FILE) -> TypeFilter:
    """The type allowlist: `.fux/config/formats.toml`, which is required.

    ⚠ **Absent meant the built-in default until W-225 stage 4a** (SR-LAW-12).
    The file now also carries the decoders' caps, which have no copy in code;
    an absent file is an error naming it, and `fux doctor --fix` writes it with
    `DEFAULT_TYPES` spelled out — what absent used to mean, now on disk. It
    still never means "index everything" (W-55) or "index nothing".

    **A leftover `.fux/sources/types` is refused** before anything is read
    (`typesfile.check_legacy`): treating it as absent would put the default in
    its place and change the index with nothing saying so.
    """
    from . import typesfile

    listed = typesfile.read(root, rel_path)
    allow = listed.allow
    if not allow:
        raise FuxError(
            f"{rel_path}: lists no file types - `include` and `[decoders]` are both empty - so "
            f"nothing would be indexed. Add at least one entry, or delete the file and run "
            f"`fux doctor --fix` to write the built-in list ({', '.join(DEFAULT_TYPES)})"
        )
    kept = readable(root, allow)
    return TypeFilter(
        allow=kept, default=False, undeclared=tuple(g for g in allow if g not in kept)
    )


def readable(root: Path, allow: tuple[str, ...]) -> tuple[str, ...]:
    """`allow` without the globs for a format no declared package reads.

    🔴 **SR-TYPES decision 1, since W-289 phase 2: the allowlist in force is
    prose plus every suffix a DECLARED package claims** (SR-PLUGINS P3) — and
    every suffix a consumer decoder in `.fux/decoders/` claims, which a
    `.fux/config/formats.toml` line already had to admit. A `*.pdf` glob in a
    repository that declares no `fux-decoder-pdf` admits nothing: the file is
    never read as prose (its bytes are a PDF) and never decoded (nothing
    declared can), so it is not walked at all. ⚠ **Not silent**: `fux ingest`
    prints the count per suffix on stderr, naming the package, and `fux doctor`
    has a row for it (P5).

    🔴 **Such a file is NOT a skip**, and so never reaches the `.fuxignore`
    blocks `skipnotice` writes: a generated line there would freeze the
    verdict, and declaring the package later would read nothing. It is simply
    not walked — and counted (`plugins.notes`).

    The seeded file spells out every first-party binding, so declaring a
    package later is the whole change — nobody edits this list to start
    reading a format fux already wrote down.
    """
    from . import typesfile

    first_party = set(decode_mod.builtin_extensions())
    claimed = decode_mod.registry(root)
    out = []
    for glob in allow:
        ext = typesfile.pattern_extension(glob)
        if ext is not None and f".{ext}" in first_party and f".{ext}" not in claimed:
            continue
        out.append(glob)
    return tuple(out)


def walk_sources(
    root: Path,
    dirs: list[str],
    *,
    types: TypeFilter | None = None,
    ignores: fuxignore.Ignores | None = None,
) -> tuple[list[WalkedFile], list[Skipped]]:
    """Walk the listed roots, honour `.fuxignore`, keep only document types.

    `types` and `ignores` default to "everything allowed, no opinions" so a
    test can exercise one condition at a time — but **no such caller ships**:
    `ingest` passes both.

    **`ignores` is checked first and can end the question in either
    direction** (SR-FUXIGNORE decision 4). An empty `Ignores` — which is what
    a repo with no `.fuxignore` produces — is indistinguishable from not
    passing one, so the old two-condition behaviour is exactly what a repo that
    has not adopted the file still gets.
    """
    ignores = ignores if ignores is not None else fuxignore.Ignores()
    files: dict[str, bytes] = {}
    #: rel -> (reason, kind). The kind is decided at the point of the skip.
    skipped: dict[str, tuple[str, str]] = {}

    def prune(directory: Path) -> bool:
        rel_dir = unicodedata.normalize("NFC", directory.relative_to(root).as_posix())
        verdict = ignored_dir(ignores, rel_dir)
        if verdict is None:
            return False
        skipped.setdefault(rel_dir + "/", (verdict.reason(), POLICY))
        return True

    for entry in dirs:
        base = root / entry
        if not base.exists():
            raise FuxError(f"configured source not found: {entry!r} (looked in {base})")
        for path in _candidate_paths(base, prune):
            # NFC, the same normalization `parse.py` applies to file content
            # (the R1/macOS-checkout hazard): a filesystem may return a path
            # in NFD even when the file was created and committed as NFC, so
            # the same document's `rel_path`/`loc` would differ by checkout
            # machine without this — a byte-identical-index guarantee (L4)
            # that a path string, not just content, has to hold too.
            rel = unicodedata.normalize("NFC", path.relative_to(root).as_posix())
            if rel in files or rel in skipped:
                continue  # already covered by an earlier, overlapping entry

            # `.fuxignore` first, and its answer is final in BOTH directions.
            # An explicit `!` re-include is the one thing that outranks the
            # type allowlist, which is why `reincluded` is a distinct state
            # from "no rule matched" rather than a bool for "not ignored".
            verdict = ignores.decide(rel, is_dir=False, hand_only=False)
            if verdict.ignored:
                # A fux-written block line carries BOTH halves forward: its
                # note is the reason that put it there, and which block it
                # sits in is its class. Neither is re-derived, so a second run
                # reports exactly what the first one found rather than
                # *"because .fuxignore says so"*.
                skipped[rel] = (verdict.reason(), _generated_kind(verdict))
                continue
            if not verdict.reincluded:
                if types is not None and not types.accepts(rel):
                    if types.awaits_package(rel):
                        continue  # W-289 P5: counted on stderr, never a frozen skip
                    skipped[rel] = ("not an indexed file type", POLICY)
                    continue

            # Past this line nothing a human wrote is in play any more: the
            # bytes themselves decide, so every skip below is UNREADABLE.
            content = path.read_bytes()
            reason = _skip_reason(content, rel, root)
            if reason == fixed("plugins", "skip_undeclared"):
                continue  # W-289 P5, as above: counted, never written down
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


def ignored_dir(ignores: fuxignore.Ignores, rel_dir: str) -> "fuxignore.Verdict | None":
    """The verdict that ignores directory `rel_dir`, when a HAND-written line does.

    🔴 **Exact, not an approximation.** `Ignores.decide` walks a file's
    ancestors shallowest-first and stops at the first one ignored, so a file
    beneath an ignored directory is ignored whatever follows — git's rule. The
    walk may therefore skip the directory without listing it, and must: W-244
    found the walk listing `work/golden/` while the tree was LOCKED (L11
    decision 9 — filtering the output does not stop the walk reading).

    **Hand lines only.** A fux-written block line is an exact path a previous
    run recorded, never a directory pattern somebody meant.
    """
    verdict = ignores.decide(rel_dir, is_dir=True, hand_only=True)
    return verdict if verdict.ignored else None


def _candidate_paths(base: Path, prune=None):
    """Every file under `base`, dot-paths excluded.

    🔴 **A directory `prune` returns True for is never entered** (W-244). An
    `rglob` enumerated everything and filtered after, so the walk listed
    `work/golden/` — the sealed answer key's parent — while the tree was LOCKED,
    and wrote the key's file NAMES into `.fux/.fuxignore` (L11 decision 9:
    filtering the output does not stop the walk reading). `os.walk` with
    `followlinks=False` is `rglob`'s own symlink behaviour, so nothing else moves.
    """
    if base.is_file():
        yield base
        return
    for dirpath, dirnames, filenames in os.walk(base):
        here = Path(dirpath)
        # dotfiles/dotdirs (.git, .DS_Store, …) are never doc content
        dirnames[:] = sorted(
            d for d in dirnames if not d.startswith(".") and not (prune is not None and prune(here / d))
        )
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            path = here / name
            if path.is_file():
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
    if rel and root is not None:
        # W-289: a format a first-party package reads, admitted by a glob
        # `readable()` cannot see through (`docs/*.json`), with no declared
        # package. Never read as prose — the bytes are that format's.
        dot = rel.rfind(".")
        suffix = rel[dot:].lower() if dot > rel.rfind("/") + 1 else ""
        if suffix and suffix in decode_mod.builtin_extensions():
            return fixed("plugins", "skip_undeclared")
    if b"\x00" in content:
        return "binary"
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return "non-utf8"
    return None
