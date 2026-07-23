"""`.fux/state/` — the committed lean plane (handoff 0004 §C, proposal §8c).

~200 bytes per document: a 32 B FuxVec code, a Bloom term signature, and a
compressed metadata record. At that size the plane is small enough to *commit*,
which is the point — `git clone` lands a corpus that already answers doc-level
queries, before anything has been ingested, and `git log .fux/state/` becomes
the history of what the corpus knew.

The design flip that makes it work: **sources are the storage.** Because Fux's
converters are deterministic and `fux.lock` records each source's sha,
re-deriving a document's text yields the exact bytes the index was built from.
So the plane stores only how to *find, verify and re-derive* — never the text.

Written in the same ingest scope as `fux.lock`, so state and lock cannot
disagree; `fux ingest --check` proves it (the STATE-DESYNC leg).
"""

from __future__ import annotations

from pathlib import Path

from . import bloom, format as fmt

STATE_REL = ".fux/state"

__all__ = [
    "STATE_REL", "state_root", "exists", "write_state", "load_state",
    "DocState", "desync_against_lock", "bloom",
]


class DocState:
    """One document as the committed plane knows it."""

    __slots__ = ("doc_id", "sha12", "title", "flags", "code", "sig", "superseded_by")

    def __init__(self, doc_id: str, sha12: str, title: str, flags: list[str],
                 code: bytes | None, sig: bytes, superseded_by: str | None = None):
        self.doc_id = doc_id
        self.sha12 = sha12
        self.title = title
        self.flags = flags
        self.code = code
        self.sig = sig
        # The *resolved terminal* doc id in a supersession chain — absent for
        # every document that isn't marked superseded (zero-cost: an optional
        # key in an already-arbitrary JSON meta payload, not a fixed field).
        self.superseded_by = superseded_by

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"DocState({self.doc_id!r}, sha12={self.sha12!r})"


def state_root(root: Path) -> Path:
    return root / STATE_REL


def exists(root: Path) -> bool:
    return state_root(root).is_dir()


def write_state(root: Path, docs: list[DocState]) -> int:
    """Rewrite the sharded plane. Returns the number of documents persisted.

    Buckets are rewritten wholesale rather than patched: at ~80 KB per bucket
    the cost is trivial, and a full rewrite is what guarantees the file has no
    memory of documents that no longer exist.
    """
    base = state_root(root)
    codes: dict[str, list] = {}
    sigs: dict[str, list] = {}
    metas: dict[str, list] = {}
    for doc in docs:
        bucket = fmt.bucket_of(doc.doc_id)
        dh = fmt.doc_hash(doc.doc_id)
        if doc.code is not None:  # no vector → no code; never a fake all-zero one
            codes.setdefault(bucket, []).append((dh, doc.code))
        sigs.setdefault(bucket, []).append((dh, doc.sig))
        payload = {"id": doc.doc_id, "sha12": doc.sha12, "title": doc.title,
                   "flags": sorted(doc.flags)}
        if doc.superseded_by:
            payload["superseded_by"] = doc.superseded_by
        metas.setdefault(bucket, []).append((dh, payload))

    for family, groups, pack in (
        ("codes", codes, fmt.pack_codes),
        ("sigs", sigs, fmt.pack_sigs),
        ("meta", metas, fmt.pack_meta),
    ):
        want = {f"{b}.bin" for b in groups}
        directory = base / family
        for bucket, records in groups.items():
            fmt.write_bucket(directory / f"{bucket}.bin", pack(records))
        if directory.is_dir():  # prune buckets that emptied out
            for path in directory.glob("*.bin"):
                if path.name not in want:
                    path.unlink()
    return len(docs)


def load_state(root: Path) -> dict[str, DocState]:
    """Read the whole plane back, keyed by doc id. Empty when nothing is committed."""
    base = state_root(root)
    if not base.is_dir():
        return {}
    out: dict[str, DocState] = {}
    by_hash_code: dict[int, bytes] = {}
    by_hash_sig: dict[int, bytes] = {}
    for path in sorted((base / "codes").glob("*.bin")) if (base / "codes").is_dir() else []:
        by_hash_code.update(fmt.unpack_codes(path.read_bytes(), f"codes/{path.name}"))
    for path in sorted((base / "sigs").glob("*.bin")) if (base / "sigs").is_dir() else []:
        by_hash_sig.update(fmt.unpack_sigs(path.read_bytes(), f"sigs/{path.name}"))
    for path in sorted((base / "meta").glob("*.bin")) if (base / "meta").is_dir() else []:
        for dh, payload in fmt.unpack_meta(path.read_bytes(), f"meta/{path.name}").items():
            out[payload["id"]] = DocState(
                doc_id=payload["id"],
                sha12=payload.get("sha12", ""),
                title=payload.get("title", ""),
                flags=list(payload.get("flags", [])),
                code=by_hash_code.get(dh),
                sig=by_hash_sig.get(dh, b""),
                superseded_by=payload.get("superseded_by"),
            )
    return out


def doc_state_from(doc_id: str, sha256: str, title: str, flags: list[str],
                   terms, code: bytes | None, superseded_by: str | None = None) -> DocState:
    return DocState(
        doc_id=doc_id,
        sha12=sha256[:12],
        title=title,
        flags=flags,
        code=code,
        sig=bloom.build(terms),
        superseded_by=superseded_by,
    )


def desync_against_lock(root: Path, records: dict[str, dict]) -> list[tuple[str, str]]:
    """Committed state vs `fux.lock` — the third leg of `fux ingest --check`.

    Catches the failure a two-way check cannot see: state committed against an
    older revision of the sources. An absent plane is not a desync — committing
    state is a choice, not an obligation.
    """
    if not exists(root):
        return []
    state = load_state(root)
    out: list[tuple[str, str]] = []
    for doc_id in sorted(set(state) | set(records)):
        entry = state.get(doc_id)
        record = records.get(doc_id)
        if entry is None:
            out.append((doc_id, "in fux.lock but missing from `.fux/state/`"))
        elif record is None:
            out.append((doc_id, "in `.fux/state/` but missing from fux.lock"))
        elif record.get("sha256", "")[:12] != entry.sha12:
            out.append((doc_id, "state built from a different revision of this source"))
    return out
