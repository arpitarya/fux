"""Chunk-vector cache: `.fux/index/vectors.bin`, invalidated with the index.

Single packed file (handoff 0003 open question 2: shards buy nothing — the
whole set is rewritten from in-memory state anyway, and one file keeps the
derived-artifact story simple). Reuse is keyed on (source sha, fidelity),
mirroring the chunk-index reuse, so `--advanced` upgrades re-embed. Vectors
are derived data: regenerable from the cache, safe to gitignore (ADR 0006
documents both modes).
"""

from __future__ import annotations

import struct
from math import sqrt
from pathlib import Path

from ..config import Config
from .model import Vec, get_model

MAGIC = b"FUXVEC1\0"
VECTORS_REL = ".fux/index/vectors.bin"


def vectors_path(root: Path) -> Path:
    return root / VECTORS_REL


def build_vectors(config: Config) -> int:
    """Embed chunks for every indexed file (reusing unchanged); returns #embedded."""
    if not config.hybrid.enabled:
        return 0
    model = get_model()
    if model is None:  # bundle not shipped: hybrid quietly unavailable
        return 0
    from ..index import store as index_store

    files = index_store.load(config.root)
    prev = load_vectors(config.root)
    out: dict[str, dict] = {}
    embedded = 0
    for rel in sorted(files):
        meta = files[rel]
        cached = prev.get(rel)
        if (
            cached
            and cached["sha"] == meta["sha256"]
            and cached["fidelity"] == meta.get("fidelity", "inferred")
            and len(cached["vecs"]) == len(meta["chunks"])
        ):
            out[rel] = cached
            continue
        vecs = [
            model.embed(f"{chunk['heading']}\n{chunk['text']}") for chunk in meta["chunks"]
        ]
        out[rel] = {
            "sha": meta["sha256"],
            "fidelity": meta.get("fidelity", "inferred"),
            "vecs": vecs,
        }
        embedded += len(vecs)
    save_vectors(config.root, out, dim=model.dim)
    return embedded


def save_vectors(root: Path, data: dict[str, dict], dim: int) -> None:
    path = vectors_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = [MAGIC, struct.pack("<III", 1, dim, len(data))]
    for rel in sorted(data):
        entry = data[rel]
        rel_raw = rel.encode("utf-8")
        sha_raw = entry["sha"].encode("ascii")
        fid_raw = entry["fidelity"].encode("utf-8")
        parts.append(struct.pack("<H", len(rel_raw)) + rel_raw)
        parts.append(struct.pack("<H", len(sha_raw)) + sha_raw)
        parts.append(struct.pack("<H", len(fid_raw)) + fid_raw)
        parts.append(struct.pack("<I", len(entry["vecs"])))
        for vec in entry["vecs"]:
            if vec is None:  # all-OOV chunk: present flag 0
                parts.append(b"\x00")
            else:
                parts.append(b"\x01" + struct.pack("<f", vec.scale))
                parts.append(struct.pack(f"{dim}b", *vec.q))
    blob = b"".join(parts)
    if not path.is_file() or path.read_bytes() != blob:
        path.write_bytes(blob)


def load_vectors(root: Path) -> dict[str, dict]:
    path = vectors_path(root)
    if not path.is_file():
        return {}
    data = path.read_bytes()
    if data[:8] != MAGIC:
        return {}  # stale/corrupt derived data: rebuild on next ingest
    try:
        version, dim, nfiles = struct.unpack_from("<III", data, 8)
        if version != 1:
            return {}
        offset = 20
        out: dict[str, dict] = {}
        for _ in range(nfiles):
            rel, offset = _read_str(data, offset)
            sha, offset = _read_str(data, offset)
            fidelity, offset = _read_str(data, offset)
            (nvecs,) = struct.unpack_from("<I", data, offset)
            offset += 4
            vecs: list[Vec | None] = []
            for _ in range(nvecs):
                present = data[offset]
                offset += 1
                if not present:
                    vecs.append(None)
                    continue
                (scale,) = struct.unpack_from("<f", data, offset)
                offset += 4
                q = struct.unpack_from(f"{dim}b", data, offset)
                offset += dim
                norm = sqrt(sum(x * x for x in q))
                vecs.append(Vec(q=tuple(q), scale=scale, norm=norm))
            out[rel] = {"sha": sha, "fidelity": fidelity, "vecs": vecs}
        return out
    except (struct.error, IndexError, UnicodeDecodeError):
        return {}


def _read_str(data: bytes, offset: int) -> tuple[str, int]:
    (length,) = struct.unpack_from("<H", data, offset)
    offset += 2
    return data[offset : offset + length].decode("utf-8"), offset + length
