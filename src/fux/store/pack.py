"""`fux pack` -- the publish path for a package author (W-302, SR-PKG-INDEX).

Copies the committed shards and the `identifiers.toml` in force into `<outdir>`
and writes the manifest beside them. **Read-only on `.fux/` by construction**:
it ingests nothing, fetches nothing, and writes nothing under the repository's
`.fux/`. Everything is checked BEFORE the first byte is written, so a refusal
leaves `<outdir>` as it was.

The digest is `plugins.segment_digest` -- the one implementation, shared with
the `kind = "index"` pin's verification; nothing here computes a hash.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from ..constants import fixed
from ..errors import FuxError
from . import dirty, fuxdir
from .format import index_dir
from .reader import iter_shard_paths, read_shard


def parse_content(spec: str | None) -> tuple[str, str]:
    """`NAME@VERSION` -> `(name, version)`; the last `@` splits (scoped npm names)."""
    if not spec:
        raise FuxError("`fux pack` needs --content NAME@VERSION -- the package that ships this segment")
    name, sep, version = spec.rpartition("@")
    if not sep or not name or not version or re.search(r"\s", spec):
        raise FuxError(f"--content {spec!r}: expected NAME@VERSION, for example my-docs-index@1.2.0")
    return name, version


def _git_uncommitted(root: Path, paths: list[Path]) -> list[str]:
    """Paths among `paths` git reports as modified or untracked.

    Empty when git cannot tell (not a work tree, git absent): the dirty list is
    the check that still runs there.
    """
    rels = [p.relative_to(root).as_posix() for p in paths]
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--", *rels],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
    except OSError:
        return []
    if done.returncode != 0:
        return []
    return sorted(line[3:] for line in done.stdout.splitlines() if line.strip())


def _check(root: Path, outdir: Path) -> tuple[list[Path], int]:
    """Every refusal, in order. Returns the shard paths and the document count."""
    from ..text import identifiers
    from .format import IDENTIFIERS_KEY, header_for

    fux = fuxdir.fux_dir(root).resolve()
    if outdir == fux or fux in outdir.parents:
        raise FuxError(f"{outdir}: pack writes outside .fux/, never into it")
    shards = iter_shard_paths(root)
    if not shards:
        raise FuxError(f"{index_dir(root)}: no index to pack -- run `fux ingest` first")
    pending = dirty.read(root)
    if pending:
        raise FuxError(
            f"the index is dirty: {len(pending)} document(s) changed since the last ingest "
            f"(first: {pending[0]}) -- run `fux ingest`, commit, and pack again"
        )
    ids_path = identifiers.path(root)
    loose = _git_uncommitted(root, [*shards, ids_path])
    if loose:
        shown = ", ".join(loose[:3]) + (" ..." if len(loose) > 3 else "")
        raise FuxError(f"uncommitted index files ({shown}) -- commit the index, then pack it")
    rules = identifiers.for_root(root)  # raises if identifiers.toml is missing
    expected = header_for(rules.digest)
    docs = 0
    for shard in shards:
        header, records = read_shard(shard)  # raises on a header this reader refuses
        if header != expected:
            what = "identifier-family digest" if header.get(IDENTIFIERS_KEY) != expected.get(IDENTIFIERS_KEY) else "header"
            raise FuxError(
                f"{shard.name}: foreign {what} -- the shard was not written by this engine "
                f"from the identifiers.toml in force; run `fux ingest`"
            )
        urls = [r.get("id") for r in records if str(r.get("id", "")).startswith("url:")]
        if urls:
            raise FuxError(f"{shard.name}: url: record {urls[0]!r} -- a package segment holds file: records only")
        docs += len(records)
    return shards, docs


def write_segment(root: Path, outdir: Path, content: tuple[str, str], *, npm: str | None = None, pypi: str | None = None) -> dict:
    """Pack the committed index at `root` into `outdir`; return the manifest.

    `content` is `(name, version)`; `npm` and `pypi` default to `name`.
    """
    from .. import __version__
    from ..plugins import segment_digest
    from ..text import identifiers
    from .reader import index_header

    outdir = Path(outdir).resolve()
    name, version = content
    shards, docs = _check(root, outdir)

    shard_dir = outdir / fixed("plugins.index", "pack_index_dir")
    for stale in shard_dir.glob("*" + fixed("index", "shard_suffix")) if shard_dir.is_dir() else ():
        stale.unlink()
    shard_dir.mkdir(parents=True, exist_ok=True)
    for shard in shards:
        shutil.copyfile(shard, shard_dir / shard.name)
    shutil.copyfile(identifiers.path(root), outdir / fixed("plugins.index", "pack_identifiers"))

    digest = segment_digest(outdir)
    keys = fixed("plugins.index", "pack_content_keys")
    values = {"npm": npm or name, "pypi": pypi or name, "version": version}
    manifest = {
        "fux_version": __version__,
        "index_header": index_header(root),
        "content": {k: values[k] for k in keys},
        "docs": docs,
        "digest": digest,
    }
    (outdir / fixed("plugins.index", "manifest")).write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest
