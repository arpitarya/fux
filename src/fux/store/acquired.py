"""`.fux/acquired/` — the bytes a fetch actually returned, kept on disk.

## A third category, and the reason it is not a fourth subdirectory of runtime

`fuxdir.py` declares every child of `.fux/` as **committed** (belongs in git) or
**derived** (gitignored, and rebuildable from committed bytes by `fux build`).
An acquired blob is neither. It is gitignored like a derived plane, and it is
**not rebuildable** — only re-*acquirable*, and only while the source still
exists and the session that reached it still holds. Putting it under
`runtime/` would file it under a contract it cannot honour: `fux build` can
reconstruct everything there, and it can never reconstruct this.

## What it buys

`refer` can only verify a `url:` document by fetching it again, so a
disconnected or signed-out session degrades every citation to `unverified` —
the weakest verdict, and indistinguishable from never having looked. With the
bytes on disk the comparison is against *the exact input the record was built
from*, which is a stronger claim than comparing two fetches: `refer/source.py`
verifies with the same fetcher a document was ingested with precisely because
*a document fetched two ways is two documents*.

⚠ **Retention is opt-in per line and defaults to OFF.** A repo that never
writes `keep=true` pays nothing, and nothing is retained by accident — the
same shape `archived` and `enrich` already have, for the same reason: what
lands on disk is a decision a human writes in a diffable line.

## Content-addressed, and the manifest is the only index

Blobs live at `objects/<sha256[:2]>/<sha256><ext>`, sharded the way the index
itself is. The url -> sha map lives in `manifest.json` **inside this plane**,
never on the committed record.

⚠ **That placement is a correctness decision, not a filing preference.** A
blob sha on a committed record states a fact that is true on one machine: two
developers pull the same repo, one has the bytes, and the record claims both
do. Keeping the map here — gitignored, advisory, exactly as `url-state.json`
is — means the record shape does not change at all, and deleting this
directory deletes the whole feature rather than orphaning a field.

## No wall clock

`run_seq` and byte counts only, the same rule `maintain/urlstate.py` follows
and for the same reason: wall clock lives in `refer/fetchcache.py`'s TTL store
and nowhere else.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

#: The plane's directory name under `.fux/`.
DIR_NAME = "acquired"

#: Where the url -> sha map lives. **Inside the plane**, so that removing the
#: directory removes the feature whole.
MANIFEST_NAME = "manifest.json"

OBJECTS_DIR = "objects"

#: The manifest's declared shape, versioned like every other file fux writes.
SCHEMA = "fux.acquired.v1"


@dataclass(frozen=True)
class Blob:
    """One retained response."""

    url: str
    sha: str
    content_type: str
    bytes: int
    #: The `run_seq` this blob was retained in. **A counter, never a clock** --
    #: it is the eviction order, and `maintain/urlstate.py` states why the
    #: distinction is a law rather than a preference. `None` means the entry
    #: predates the field, which sorts oldest.
    run_seq: int | None = None

    def as_json(self) -> dict:
        out = {"sha": self.sha, "content_type": self.content_type, "bytes": self.bytes}
        if self.run_seq is not None:
            out["run_seq"] = self.run_seq
        return out


def plane(root: Path) -> Path:
    """`.fux/acquired/`. **Pure — returns a path, creates nothing.**

    ⚠ Creating on read was the first version and it was wrong: asking where
    the manifest lives would conjure the plane into existence in a repo that
    had never opted in, and `fux doctor` would then report a directory the
    consumer never asked for. Writers call `ensure_plane`; readers do not.
    """
    return root / ".fux" / DIR_NAME


def ensure_plane(root: Path) -> Path:
    """Create the plane and tag it. Called only on the write path.

    ⚠ **`CACHEDIR.TAG` is not decoration.** ADR-CACHEDIR-TAG puts it on every
    gitignored plane so backup tools, `tar --exclude-caches` and Time Machine
    skip it without being told. A plane holding retained SOURCE BYTES is
    exactly the directory a consumer least wants silently swept into a backup,
    which makes the tag matter more here than it does for `runtime/`.
    """
    path = plane(root)
    path.mkdir(parents=True, exist_ok=True)
    tag = path / "CACHEDIR.TAG"
    if not tag.exists():
        from . import fuxdir

        tag.write_bytes(fuxdir.CACHEDIR_TAG.encode("ascii"))
    return path


def manifest_path(root: Path) -> Path:
    return plane(root) / MANIFEST_NAME


def blob_path(root: Path, sha: str, ext: str = "") -> Path:
    """`objects/<sha[:2]>/<sha><ext>` — sharded like the index, for the same
    reason: one directory holding ten thousand files is a directory no tool
    enjoys walking."""
    return plane(root) / OBJECTS_DIR / sha[:2] / f"{sha}{ext}"


def sha_of(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


# -- reading ----------------------------------------------------------------


def read_manifest(root: Path) -> dict[str, Blob]:
    """url -> Blob. A missing, truncated or corrupt manifest reads as empty.

    **Advisory, exactly like the dirty list and `url-state.json`.** Nothing
    here may take down a run: the worst a broken manifest can do is make fux
    re-fetch and re-write bytes it already had.
    """
    path = manifest_path(root)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, dict):
        return {}
    out: dict[str, Blob] = {}
    for url, rec in entries.items():
        if not isinstance(rec, dict):
            continue
        sha = rec.get("sha")
        if not isinstance(sha, str) or len(sha) != 64:
            continue
        out[url] = Blob(
            url=url,
            sha=sha,
            content_type=rec.get("content_type") if isinstance(rec.get("content_type"), str) else "",
            bytes=rec.get("bytes") if isinstance(rec.get("bytes"), int) else 0,
            run_seq=rec.get("run_seq") if isinstance(rec.get("run_seq"), int) else None,
        )
    return out


def stored(root: Path, url: str) -> Path | None:
    """The blob file for `url`, or `None` when it is not on disk.

    ⚠ **Checks the FILE, not just the manifest.** A manifest entry whose blob
    was deleted by hand is a claim this plane cannot honour, and a caller that
    trusted it would read a missing path.
    """
    blob = read_manifest(root).get(url)
    if blob is None:
        return None
    for path in plane(root).joinpath(OBJECTS_DIR, blob.sha[:2]).glob(f"{blob.sha}*"):
        return path
    return None


# -- writing ----------------------------------------------------------------


def save(
    root: Path, url: str, raw: bytes, content_type: str, ext: str = "", run_seq: int | None = None
) -> Blob:
    """Write `raw` into the plane and return its record.

    ⚠ **Writes the blob, never the manifest.** `fetch_all` runs under a thread
    pool and a per-fetch manifest write is a corruption; the caller collects
    the returned `Blob`s and calls `write_manifest` once, single-threaded, at
    the end of the run.

    Content addressing makes a re-fetch of unchanged bytes a no-op: the path
    already exists and is left alone rather than rewritten.
    """
    ensure_plane(root)
    sha = sha_of(raw)
    path = blob_path(root, sha, ext)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        # Temp-then-rename: `fetch` is concurrent, and a reader must never see
        # a half-written blob at a name that claims to be a content address.
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".part")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(raw)
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    return Blob(url=url, sha=sha, content_type=content_type, bytes=len(raw), run_seq=run_seq)


def write_manifest(root: Path, blobs: dict[str, Blob]) -> None:
    """Replace the manifest. Called once per run, never per fetch.

    Sorted by URL so the file is stable: this plane is gitignored, but a file
    whose byte order changes on every run is one nobody can diff while
    debugging, and debugging is most of what it is for.
    """
    if not blobs and not manifest_path(root).exists():
        # Nothing to record and nothing recorded: do not conjure the plane.
        return
    # ⚠ **An EMPTY manifest is still written when one already exists.** The
    # first version returned early on any empty dict, so removing the last
    # retained URL left its entry on disk forever -- `fux remove` reported
    # success while the plane kept claiming to hold a document nobody listed.
    # "Nothing to write" and "write nothing" are not the same instruction.
    ensure_plane(root)
    path = manifest_path(root)
    body = {
        "schema": SCHEMA,
        "entries": {url: blobs[url].as_json() for url in sorted(blobs)},
    }
    text = json.dumps(body, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".part")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


#: The store's default ceiling, and the reason `keep` may default to true.
#:
#: **A judgement, not a measurement.** Large enough that an ordinary corpus of
#: documents never reaches it, small enough that a runaway one is noticed as a
#: bounded number rather than a full disk. `[sources.url] acquired_max_bytes`
#: overrides it.
DEFAULT_MAX_BYTES = 2 * 1024 * 1024 * 1024


def blobs_on_disk(root: Path) -> list[tuple[Path, int]]:
    """Every stored blob and its size. Sorted for determinism, not for policy."""
    objects = plane(root) / OBJECTS_DIR
    if not objects.is_dir():
        return []
    return sorted(
        ((p, p.stat().st_size) for p in objects.rglob("*") if p.is_file()),
        key=lambda pair: str(pair[0]),
    )


def sweep(root: Path, blobs: dict[str, Blob]) -> int:
    """Delete blobs no URL points at. Returns how many went.

    **Unreferenced, not old.** A blob nobody references is unreachable by
    construction -- `fux remove` dropped its line, or a re-fetch superseded it
    -- so removing it loses nothing that could still be cited. That is a
    different act from eviction, which removes something still referenced, and
    the two are kept apart deliberately.
    """
    referenced = {b.sha for b in blobs.values()}
    gone = 0
    for path, _ in blobs_on_disk(root):
        if path.name.split(".", 1)[0] not in referenced:
            try:
                path.unlink()
                gone += 1
            except OSError:
                pass
    return gone


def evict(
    root: Path,
    blobs: dict[str, Blob],
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    protected: set[str] | None = None,
) -> list[str]:
    """Bring the store under `max_bytes`. Returns the URLs whose blob went.

    ⚠ **`protected` is not an optimisation; it is the whole safety property.**
    An acquired blob is not rebuildable -- only re-acquirable, and only while
    the source is still reachable and the session still holds. A URL whose
    last fetch FAILED is precisely the one that cannot be got back, so it is
    never chosen, however large or however old. Eviction may only remove what
    a re-fetch could restore.

    ⚠ **Order is by `run_seq`, never by mtime.** This plane holds no wall
    clock (`maintain/urlstate.py`'s rule), and reading the filesystem's clock
    to decide would smuggle one in through the back door. A blob with no
    recorded `run_seq` sorts oldest -- it predates the counter, so it is the
    least evidence of recent use there is -- with the URL as a tie-break so
    two blobs from one run evict in a stable order.
    """
    protected = protected or set()
    total = total_bytes(root)
    if total <= max_bytes:
        return []

    order = sorted(
        (u for u in blobs if u not in protected),
        key=lambda u: (blobs[u].run_seq if blobs[u].run_seq is not None else -1, u),
    )
    evicted: list[str] = []
    for url in order:
        if total <= max_bytes:
            break
        blob = blobs[url]
        for path, size in blobs_on_disk(root):
            if path.name.split(".", 1)[0] == blob.sha:
                try:
                    path.unlink()
                except OSError:
                    continue
                total -= size
                break
        evicted.append(url)
    return evicted


def total_bytes(root: Path) -> int:
    """How much this plane is holding. For `fux doctor` to report."""
    objects = plane(root) / OBJECTS_DIR
    if not objects.is_dir():
        return 0
    return sum(p.stat().st_size for p in objects.rglob("*") if p.is_file())
