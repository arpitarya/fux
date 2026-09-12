"""The canonical reader: shard files in, `(header, records)` out.

Permissive about record content (readers must accept both `meta:"plain"` and
`meta:"hashed"` forms from day one — §7), strict about shape: every shard
must open with a valid `_format` header pinning the same schema/analyzer/
tf-field order this reader was built for, or the shard is refused rather than
silently misread (a reversed `tf_fields`, for instance, would invert every
heading/body tf with no error anywhere downstream).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..errors import FuxError
from .format import HEADER, index_dir, shard_for

_SHARD_NAME_RE = re.compile(r"[0-9a-f]{2}\.jsonl")


def iter_shard_paths(root: Path) -> list[Path]:
    directory = index_dir(root)
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.jsonl") if _SHARD_NAME_RE.fullmatch(p.name))


def raw_record_lines(path: Path) -> tuple[dict, list[bytes]]:
    """Header-validated record lines, NOT JSON-parsed — for the B2 byte-level
    prefilter scan (`query/`), which must avoid `json.loads` on every line;
    only lines that pass the prefilter get parsed by the caller.
    """
    # Split on `\n` only — `str.splitlines()` also breaks on U+2028/2029/0085,
    # which `json.dumps(ensure_ascii=False)` writes raw inside a string value;
    # splitting on those would corrupt a legal record. Read bytes, not text,
    # to avoid platform newline translation entirely.
    raw = path.read_bytes()
    if not raw:
        raise FuxError(f"empty shard file: {path}")
    lines = raw.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    # ⚠ **Conflict markers FIRST, before the header is even parsed** (W-140
    # row 9, 2026-09-11). A shard git could not merge — or that the fux merge
    # driver deliberately refused — carries `<<<<<<<` on some line, and the
    # header check below then reported *not a fux index shard, or the file is
    # truncated*: a sentence that sends someone looking for corruption while
    # the real answer is an unresolved merge two commands away. Diagnosed the
    # same way `tune.toml` and `output.toml` already diagnose it, because a
    # committed file people merge will eventually carry one.
    _refuse_conflict_markers(raw, path)

    header = _load_json(lines[0], path=path, lineno=1)
    if not isinstance(header, dict) or header.get("_format") != HEADER["_format"]:
        # ⚠ **This message named neither the found value nor the expected one
        # until 2026-08-27**, while its two siblings below named both — and it
        # is the one that actually fires, because it is what an ENGINE UPGRADE
        # trips. Measured in `fux-playground`, whose committed index was
        # `fux.index.v1`: every one of 50 goldens failed with
        # `shard missing/mismatched _format header`, which reads as CORRUPTION.
        # There is no migrate verb, so a reader who concludes "my index is
        # broken" has no way to learn that the fix is a re-ingest.
        found = header.get("_format") if isinstance(header, dict) else None
        if found is None:
            # No `_format` at all: not a version skew, a file that is not a
            # shard. Saying "written by a different version" here would send
            # someone re-ingesting over what may be a truncated write.
            raise FuxError(
                f"shard {path} has no _format header on its first line — this "
                f"is not a fux index shard, or the file is truncated. A shard's "
                f"first line is always {HEADER['_format']!r}."
            )
        # 🔴 **This used to say *delete `.fux/index/` and run `fux ingest`*,
        # "which is safe because the index holds statistics, never content"**
        # (W-140 row 9, fixed 2026-09-12). It is not safe, and
        # [ADR-INDEX-LIFECYCLE] decision 10a exists BECAUSE it is not: a `url:`
        # record is the one thing in the index that is not a function of a
        # committed file, so deleting the directory destroys it and an offline
        # re-ingest cannot bring it back. `--full` was built to be this path and
        # the error pointed away from it.
        raise FuxError(
            f"shard {path} declares _format {found!r}, this engine writes "
            f"{HEADER['_format']!r} — the index was written by a different "
            f"version of fux. There is no in-place migration: run "
            f"`fux ingest --full` to rewrite it from the sources. "
            f"WARNING: do NOT delete `.fux/index/` by hand: `url:` records are the one "
            f"thing in it that no re-extraction can rebuild, and `--full` refuses "
            f"rather than stranding them, naming each one."
        )
    if header.get("analyzer") != HEADER["analyzer"]:
        raise FuxError(
            f"shard {path} was written by analyzer {header.get('analyzer')!r}, "
            f"this reader is {HEADER['analyzer']!r} — ADR-recorded analyzer bumps only"
        )
    if header.get("tf_fields") != HEADER["tf_fields"]:
        raise FuxError(
            f"shard {path} has tf_fields {header.get('tf_fields')!r}, "
            f"expected {HEADER['tf_fields']!r} — refusing to silently misread postings"
        )
    return header, lines[1:]


def _refuse_conflict_markers(raw: bytes, path: Path) -> None:
    """Name an unresolved merge as one, and name the way out.

    **Either side is a correct starting point and that is the point.** A shard
    is derived — statistics over content fux can re-derive — so taking `--ours`
    or `--theirs` loses nothing that `fux ingest` will not immediately rebuild
    from the merged working tree. That is what makes this recoverable in two
    commands rather than a decision about which colleague's index to keep.
    """
    for marker in (b"<<<<<<< ", b"=======\n", b">>>>>>> "):
        if marker in raw:
            rel = path.name
            raise FuxError(
                f"shard {path} carries unresolved merge conflict markers, so nothing "
                f"can read it. A shard is DERIVED, so either side is a fine starting "
                f"point: `git checkout --ours -- .fux/index/{rel}` (or --theirs), then "
                f"`fux ingest`, which rebuilds it from the merged content rather than "
                f"from either side's copy."
            )


def read_shard(path: Path) -> tuple[dict, list[dict]]:
    header, lines = raw_record_lines(path)
    records = [_load_json(line, path=path, lineno=i + 2) for i, line in enumerate(lines)]
    return header, records


def _load_json(line: bytes, *, path: Path, lineno: int):
    try:
        return json.loads(line)
    except json.JSONDecodeError as exc:
        raise FuxError(f"{path}:{lineno}: not valid JSON ({exc})") from exc


def read_index(root: Path) -> dict[str, dict]:
    """All records across every shard, keyed by `id`.

    Raises loudly on a doc id appearing more than once, or in a shard other
    than the one `shard_for(id)` assigns it to — both are impossible by
    construction (handoff §8) but a merge gone wrong could produce either.
    """
    out: dict[str, dict] = {}
    for path in iter_shard_paths(root):
        expected_shard = path.stem
        _, records = read_shard(path)
        for record in records:
            doc_id = record["id"]
            if shard_for(doc_id) != expected_shard:
                raise FuxError(f"{path}: record {doc_id!r} belongs in shard {shard_for(doc_id)}, not here")
            if doc_id in out:
                raise FuxError(f"duplicate id across shards: {doc_id!r}")
            out[doc_id] = record
    return out


# -- the foreign-index seam ---------------------------------------------------
#
# ADR-INDEX-LIFECYCLE decision 10 says a full re-ingest is owed on every index
# written before an analyzer bump, and names `fux ingest --full` as the command
# that discharges it. That command read the existing index unconditionally — to
# carry `url:` records forward — so **the documented migration refused the very
# index it exists to replace.** These two functions are what let `--full` treat
# a foreign index as absent without ever misreading one.
#
# The line they hold: **record identity is schema-stable; record content is
# not.** `id` has meant the same thing since v1. `terms` has not — v1 hashed a
# different function over two fields where v2 hashes five. So `foreign_url_ids`
# reads `id` and refuses to touch anything else, and every other reader keeps
# refusing the shard outright.


def index_header(root: Path) -> dict | None:
    """The first shard's header, unvalidated — or `None` with no index.

    The one place a header is read *without* being required to match. Every
    other path in this module compares against `HEADER` and raises.
    """
    paths = iter_shard_paths(root)
    if not paths:
        return None
    raw = paths[0].read_bytes().split(b"\n", 1)[0]
    if not raw:
        raise FuxError(f"empty shard file: {paths[0]}")
    header = _load_json(raw, path=paths[0], lineno=1)
    return header if isinstance(header, dict) else None


def index_is_foreign(root: Path) -> bool:
    """True when an index exists that this reader refuses.

    Distinguished from "no index" deliberately: absent is a first run, foreign
    is a migration, and the two want different messages.
    """
    header = index_header(root)
    if header is None:
        return False
    return any(header.get(k) != HEADER[k] for k in ("_format", "analyzer", "tf_fields"))


def foreign_url_ids(root: Path) -> list[str]:
    """`url:` ids inside an index this reader refuses.

    **Why this is safe when `read_shard` is not:** it parses each line and
    reads `id` — a field whose meaning has not changed across any schema
    version — and reads nothing else. It never touches `terms`, whose meaning
    is exactly what the refused header says has changed.

    **Why it exists:** a `file:` record is a pure function of a committed file,
    so discarding one costs a re-extraction and nothing more. A `url:` record
    is the only thing in the index that came from the network, cannot be
    rebuilt offline, and would be **silently lost** by a migration that simply
    deleted the old shards. This is the list `--full` refuses to strand.
    """
    out: list[str] = []
    for path in iter_shard_paths(root):
        lines = path.read_bytes().split(b"\n")
        for lineno, line in enumerate(lines[1:], start=2):
            if not line or b'"url:' not in line:
                continue
            record = _load_json(line, path=path, lineno=lineno)
            if isinstance(record, dict) and str(record.get("id", "")).startswith("url:"):
                out.append(record["id"])
    return sorted(out)
