"""W-302 step 5 — the index-package round trip, as a user, through the real CLI.

An author ingests a docs repository and runs `fux pack`; the segment is installed
as the index package `acme-docs-index` and the docs as `acme-docs` (the package
the manifest's `content` names); a consumer pins the segment in
`.fux/config/plugins.toml` (W-299), finds a package document with `fux ask`
(W-300's merged query), and reads its passage with `fux_passage` at the hit's
`pkg:` location (W-301) — read in place, inside the installed docs package.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from l12_fixtures import config_file, write_config, write_dirs

from fux.plugins import segment_digest

VERSION = "1.2.0"
DOCS = {
    "rota.md": "# Rota\n\nthe rota hands over Monday\n",
    "runbook.md": "# Runbook\n\nrestart the queue worker before draining the zarquon broker\n",
}


def _env(site: Path | None) -> dict:
    env = dict(os.environ)
    # The engine under test first, absolute: a relative entry would resolve
    # against the consumer's cwd and fall through to whatever fux is installed.
    engine = str(Path(__import__("fux").__file__).resolve().parents[1])
    inherited = [str(Path(p).resolve()) for p in env.get("PYTHONPATH", "").split(os.pathsep) if p]
    env["PYTHONPATH"] = os.pathsep.join([*([str(site)] if site else []), engine, *inherited])
    return env


def _fux(root: Path, *argv: str, env: dict | None = None, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *argv], capture_output=True, text=True, encoding="utf-8",
        cwd=root, env=env if env is not None else _env(None), input=stdin,
    )


def _git(root: Path, *argv: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *argv], cwd=root, check=True, capture_output=True)


def _repo(root: Path, docs: dict[str, str]) -> Path:
    root.mkdir(parents=True)
    _git(root, "init", "-q")
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    write_dirs(root, "docs\n")
    config_file(root, "pii").write_text("", encoding="utf-8")
    write_config(root)
    (root / "docs").mkdir()
    for name, text in docs.items():
        (root / "docs" / name).write_text(text, encoding="utf-8")
    return root


def _install(site: Path, name: str, version: str, files: Path, *, under: str = "") -> None:
    module = name.replace("-", "_")
    shutil.copytree(files, site / module / under if under else site / module)
    info = site / f"{module}-{version}.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n", encoding="utf-8")


def test_pack_pin_search_and_read_a_passage_in_place(tmp_path):
    # The author: ingest, commit, pack.
    author = _repo(tmp_path / "author", DOCS)
    done = _fux(author, "ingest", "--no-accelerator", "--no-progress")
    assert done.returncode == 0, done.stderr
    _git(author, "add", "-A")
    _git(author, "commit", "-q", "-m", "docs and index")
    out = tmp_path / "segment"
    done = _fux(author, "pack", str(out), "--content", f"acme-docs@{VERSION}")
    assert done.returncode == 0, done.stderr

    # Both packages installed where the consumer's interpreter resolves them.
    site = tmp_path / "site"
    _install(site, "acme-docs-index", VERSION, out)
    _install(site, "acme-docs", VERSION, author / "docs", under="docs")
    env = _env(site)

    # The consumer: its own docs, the pin, its own ingest.
    consumer = _repo(tmp_path / "consumer", {"own.md": "# Our page\n\nwe never touch the broker\n"})
    plugins_toml = config_file(consumer, "plugins")
    plugins_toml.write_text(
        (plugins_toml.read_text(encoding="utf-8") if plugins_toml.exists() else "")
        + f'\n[[package]]\nname = "acme-docs-index"\nkind = "index"\nversion = "{VERSION}"\n'
        + f'digest = "{segment_digest(out)}"\npypi = "acme-docs-index"\nnpm = "acme-docs-index"\n',
        encoding="utf-8",
    )
    done = _fux(consumer, "ingest", "--no-accelerator", "--no-progress", env=env)
    assert done.returncode == 0, done.stderr

    # Search: one ranking over the repository and the package (W-300).
    done = _fux(consumer, "ask", "restart the queue worker", "--json", env=env)
    assert done.returncode == 0, done.stderr
    hits = json.loads(done.stdout)["results"]
    assert hits, done.stderr
    assert hits[0]["id"] == "file:docs/runbook.md" and hits[0]["package"] == "acme-docs-index"
    repo_only = json.loads(_fux(consumer, "ask", "restart the queue worker", "--json", "--scope", "repo", env=env).stdout)
    assert all("package" not in h for h in repo_only["results"])

    # The passage, at the hit's `pkg:` location, over MCP (W-301).
    calls = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "fux_search", "arguments": {"query": "restart the queue worker"}}},
    ]
    done = _fux(consumer, "mcp", env=env, stdin="".join(json.dumps(c) + "\n" for c in calls))
    assert done.returncode == 0, done.stderr
    assert len(done.stdout.splitlines()) == 2, (done.stdout, done.stderr)
    search = json.loads(done.stdout.splitlines()[1])["result"]["structuredContent"]
    location = search["results"][0]["location"]
    assert location == f"pkg:acme-docs@{VERSION}#docs/runbook.md"
    passage_call = {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": "fux_passage", "arguments": {"path": location}}}
    done = _fux(consumer, "mcp", env=env, stdin=json.dumps(passage_call) + "\n")
    assert done.returncode == 0, done.stderr
    passage = json.loads(done.stdout.splitlines()[0])["result"]["structuredContent"]
    assert "restart the queue worker" in passage["text"]
    assert passage["sha"] == search["results"][0]["sha"]
