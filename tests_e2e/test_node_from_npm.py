"""The Node reader as a consumer installs it: `npm install fux-engine` (W-292).

Arpit, 2026-10-21: *"`npm install fux-engine` … will be the only way to install
the node package for fux."* So this is the one Node install path, exercised end
to end: Python's `fux setup` + `fux ingest` make a repository (and write no
Node), the published payload is built exactly as `publish.yml` builds it and
packed with `npm pack`, `npm install` puts the tarball into the repository, and
`npx fux find …` answers from the index.

**No network** (L5): the tarball is a local file, the package has no
dependencies, and both npm calls run `--offline`. Skipped where `node` or `npm`
is absent; CI's Node lane is where it runs on every OS.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from fux.store import nodebundle

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None or shutil.which("npm") is None, reason="no node/npm on PATH"
)


def _npm(*args: str, cwd: Path, env: dict) -> subprocess.CompletedProcess:
    npm = shutil.which("npm")
    return subprocess.run([npm, *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def _env(tmp: Path) -> dict:
    """npm with a scratch cache and no user config, so nothing on this machine
    — and no registry — is consulted."""
    env = {k: v for k, v in os.environ.items() if not k.lower().startswith("npm_")}
    env["npm_config_cache"] = str(tmp / "npm-cache")
    env["npm_config_userconfig"] = str(tmp / "npmrc")
    env["npm_config_audit"] = "false"
    env["npm_config_fund"] = "false"
    env["npm_config_update_notifier"] = "false"
    (tmp / "npmrc").write_text("", encoding="utf-8")
    return env


def _fux(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "fux.cli", *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8")


def test_npm_install_fux_engine_then_npx_fux_answers(tmp_path):
    env = _env(tmp_path)

    # 1. A repository, made the way a consumer makes one.
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    (repo / "docs" / "retry.md").write_text("# Retry policy\n\nhow we roll back a release\n",
                                            encoding="utf-8")
    setup = _fux(repo, "setup", "--no-agents")
    assert setup.returncode == 0, setup.stderr
    assert not (repo / ".fux" / "node").exists() and not (repo / ".fux" / "fux").exists()
    ingest = _fux(repo, "ingest")
    assert ingest.returncode == 0, ingest.stderr

    # 2. The published payload, built as publish.yml builds it, then packed.
    dist = tmp_path / "dist"
    nodebundle.write(ROOT / "node", dist)
    (dist / "package.json").write_bytes((ROOT / "node" / "package.json").read_bytes())
    packed = _npm("pack", "--offline", "--pack-destination", str(tmp_path), cwd=dist, env=env)
    assert packed.returncode == 0, packed.stderr
    tarball = next(tmp_path.glob("fux-engine-*.tgz"))

    # 3. `npm install fux-engine` — from the tarball, offline.
    (repo / "package.json").write_text(json.dumps({"name": "consumer", "private": True}) + "\n",
                                       encoding="utf-8")
    installed = _npm("install", "--offline", "--no-save", str(tarball), cwd=repo, env=env)
    assert installed.returncode == 0, installed.stderr
    assert (repo / "node_modules" / "fux-engine" / "fux.mjs").is_file()
    assert not (repo / "node_modules" / "fux-engine" / "src").exists(), "L10: no source tree"

    # 4. `npx fux find …` answers, from a subdirectory too (findRoot walks up).
    for cwd in (repo, repo / "docs"):
        found = _npm("exec", "--offline", "--no", "--", "fux", "find", "retry", cwd=cwd, env=env)
        assert found.returncode == 0, found.stderr
        assert "docs/retry.md" in found.stdout
