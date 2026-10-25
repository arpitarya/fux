"""`fux pack <outdir>` as a package author runs it -- the real CLI via subprocess.

W-302, SR-PKG-INDEX: the verb copies the committed shards and the
`identifiers.toml` in force into `<outdir>`, writes `fux-index.json`, and
refuses -- writing nothing -- on a dirty index, a foreign header, a `url:`
record, or a missing `--content`. Its digest is `plugins.segment_digest`, the
one the `kind = "index"` pin verifies.

⚠ **Step 5's round trip is partial by design**: pin (W-299), search (W-300) and
passage (W-301) are other items' verbs. This file proves pack and that the
segment it emits digests the same way the pin will verify it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from l12_fixtures import config_file, write_config, write_dirs

from fux.constants import fixed
from fux.plugins import segment_digest

SCHEMA = Path(__file__).resolve().parents[1] / "src" / "fux" / "schemas" / "fux-index.schema.json"


def _fux(root: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *argv],
        capture_output=True, text=True, encoding="utf-8", cwd=root,
    )


def _git(root: Path, *argv: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *argv],
        cwd=root, check=True, capture_output=True,
    )


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "docs-pkg"
    root.mkdir()
    _git(root, "init", "-q")
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (root / ".fux" / "sources").mkdir(parents=True)
    write_dirs(root, "docs\n")
    config_file(root, "pii").write_text("", encoding="utf-8")
    write_config(root)
    (root / "docs").mkdir()
    (root / "docs" / "rota.md").write_text("# Rota\n\nthe rota hands over Monday\n", encoding="utf-8")
    (root / "docs" / "runbook.md").write_text("# Runbook\n\nrestart the queue worker\n", encoding="utf-8")
    ingest = _fux(root, "ingest", "--no-accelerator", "--no-progress")
    assert ingest.returncode == 0, ingest.stderr
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "docs and index")
    return root


def _pack(root: Path, out: Path, *extra: str) -> subprocess.CompletedProcess:
    return _fux(root, "pack", str(out), "--content", "acme-docs@1.2.0", *extra)


def _tree(path: Path) -> dict[str, bytes]:
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in sorted(path.rglob("*")) if p.is_file()}


def test_pack_writes_the_segment_and_a_manifest_the_pin_would_verify(tmp_path):
    root = _repo(tmp_path)
    out = tmp_path / "out"
    done = _pack(root, out)
    assert done.returncode == 0, done.stderr
    manifest = json.loads((out / fixed("plugins.index", "manifest")).read_text(encoding="utf-8"))
    assert manifest["content"] == {"npm": "acme-docs", "pypi": "acme-docs", "version": "1.2.0"}
    assert manifest["docs"] == 2
    assert manifest["index_header"]["_format"].startswith("fux.index.")
    # The digest is the shared function's, over the outdir -- what W-299 verifies.
    assert manifest["digest"] == segment_digest(out)
    assert manifest["digest"].startswith(fixed("plugins", "digest_prefix"))
    shards = sorted(p.name for p in (root / ".fux" / "index").glob("*.jsonl"))
    assert sorted(p.name for p in (out / "index").iterdir()) == shards
    assert (out / "identifiers.toml").read_bytes() == (root / ".fux" / "config" / "identifiers.toml").read_bytes()
    for name in shards:
        assert (out / "index" / name).read_bytes() == (root / ".fux" / "index" / name).read_bytes()


def test_pack_is_deterministic_and_the_digest_ignores_the_manifest(tmp_path):
    root = _repo(tmp_path)
    one, two = tmp_path / "one", tmp_path / "two"
    assert _pack(root, one).returncode == 0 and _pack(root, two).returncode == 0
    assert _tree(one) == _tree(two)
    # Repacking over an existing outdir changes nothing and leaves no stale shard.
    (one / "index" / "ff.jsonl").write_text("stale\n", encoding="utf-8")
    assert _pack(root, one).returncode == 0
    assert _tree(one) == _tree(two)


def test_pack_writes_nothing_under_dot_fux(tmp_path):
    root = _repo(tmp_path)
    before = _tree(root / ".fux")
    assert _pack(root, tmp_path / "out").returncode == 0
    assert _tree(root / ".fux") == before
    refused = _pack(root, root / ".fux" / "pkg")
    assert refused.returncode == 1 and ".fux" in refused.stderr
    assert _tree(root / ".fux") == before


def test_pack_refuses_without_content(tmp_path):
    root = _repo(tmp_path)
    out = tmp_path / "out"
    done = _fux(root, "pack", str(out))
    assert done.returncode == 1 and "--content" in done.stderr
    assert not out.exists()
    bad = _fux(root, "pack", str(out), "--content", "no-version")
    assert bad.returncode == 1 and "NAME@VERSION" in bad.stderr and not out.exists()


def test_pack_refuses_a_dirty_index(tmp_path):
    root = _repo(tmp_path)
    runtime = root / ".fux" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / fixed("maintain", "dirty")).write_text("docs/rota.md\n", encoding="utf-8")
    out = tmp_path / "out"
    done = _pack(root, out)
    assert done.returncode == 1 and "dirty" in done.stderr
    assert not out.exists()


def test_pack_refuses_uncommitted_shards(tmp_path):
    root = _repo(tmp_path)
    (root / "docs" / "new.md").write_text("# New\n\nfresh words here\n", encoding="utf-8")
    assert _fux(root, "ingest", "--no-accelerator", "--no-progress").returncode == 0
    out = tmp_path / "out"
    done = _pack(root, out)
    assert done.returncode == 1 and "uncommitted" in done.stderr
    assert not out.exists()


def _recommit_with(root: Path, edit) -> None:
    shard = next((root / ".fux" / "index").glob("*.jsonl"))
    edit(shard)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "tamper")


def test_pack_refuses_a_foreign_header(tmp_path):
    root = _repo(tmp_path)

    def edit(shard: Path) -> None:
        head, _, rest = shard.read_bytes().partition(b"\n")
        header = json.loads(head)
        header["analyzer"] = "v0"
        shard.write_bytes(json.dumps(header, separators=(",", ":")).encode() + b"\n" + rest)

    _recommit_with(root, edit)
    out = tmp_path / "out"
    done = _pack(root, out)
    assert done.returncode == 1 and "error:" in done.stderr
    assert not out.exists()


def test_pack_refuses_a_url_record(tmp_path):
    root = _repo(tmp_path)

    def edit(shard: Path) -> None:
        lines = shard.read_bytes().split(b"\n")
        for i, line in enumerate(lines[1:], start=1):
            if line.startswith(b"{"):
                rec = json.loads(line)
                rec["id"] = "url:https://example.com/x"
                lines[i] = json.dumps(rec, sort_keys=True, separators=(",", ":")).encode()
                break
        shard.write_bytes(b"\n".join(lines))

    # Put a url: id in whichever shard actually holds a record.
    for shard in sorted((root / ".fux" / "index").glob("*.jsonl")):
        if len(shard.read_bytes().split(b"\n")) > 2:
            edit(shard)
            break
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "tamper")
    out = tmp_path / "out"
    done = _pack(root, out)
    assert done.returncode == 1 and "url:" in done.stderr
    assert not out.exists()


def test_manifest_validates_against_the_index_schema(tmp_path):
    if not SCHEMA.is_file():
        pytest.skip("src/fux/schemas/fux-index.schema.json is W-299's and does not exist yet")
    root = _repo(tmp_path)
    out = tmp_path / "out"
    assert _pack(root, out).returncode == 0
    manifest = json.loads((out / fixed("plugins.index", "manifest")).read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    try:
        import jsonschema
    except ImportError:
        props = schema.get("properties", schema.get("fields", {}))
        assert set(manifest) <= set(props), f"manifest keys outside the schema: {set(manifest) - set(props)}"
        return
    jsonschema.validate(manifest, schema)
