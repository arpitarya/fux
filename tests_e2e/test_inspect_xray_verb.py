"""`fux inspect --diff` as a user runs it — the decoder change that deletes an edge.

W-220's §Tests fixture, verbatim: *"`--diff` flags edge loss: fixture = an html
decoder that strips hrefs."* A consumer html decoder that throws away every
`href` looks like a tidy-up; it deletes the page's `ref` edge, and the only
thing that says so is the diff. [SR-INSPECT](../records/0156_inspect.md)
decision 21.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

STRIPPING_DECODER = '''import re

EXTENSIONS = (".html",)


def decode(raw, rel_path):
    text = re.sub(rb"<[^>]+>", b" ", raw).decode("utf-8")
    return "# Runbook\\n\\n" + " ".join(text.split())
'''


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [sys.executable, "-m", "fux.cli", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    return result


def test_a_decoder_that_strips_hrefs_is_an_edge_loss_alert(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    sources = tmp_path / ".fux" / "sources"
    sources.mkdir(parents=True)
    (sources / "dirs").write_text("docs\n", encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "target.md").write_text("# Target\n\nThe reconciliation target.\n", encoding="utf-8")
    (docs / "page.html").write_text(
        '<html><body><h1>Runbook</h1><p>See the <a href="target.md">target page</a>.</p></body></html>',
        encoding="utf-8",
    )
    _run(tmp_path, "ingest")
    _run(tmp_path, "inspect", "--json", "--no-progress", "--all")
    before = tmp_path / "before.json"
    before.write_bytes((tmp_path / ".fux" / "runtime" / "inspect" / "report.json").read_bytes())
    rows = {r["loc"]: r for r in json.loads(before.read_text())["documents"]}
    assert rows["docs/page.html"]["edges"] == [["ref", "file:docs/target.md"]]

    (tmp_path / ".fux" / "decoders").mkdir()
    (tmp_path / ".fux" / "decoders" / "html.py").write_text(STRIPPING_DECODER, encoding="utf-8")
    _run(tmp_path, "ingest")
    _run(tmp_path, "inspect", "--json", "--no-progress", "--all")
    after = tmp_path / ".fux" / "runtime" / "inspect" / "report.json"

    text = _run(tmp_path, "inspect", "--diff", str(before), str(after)).stdout
    assert "🔴 Edge loss — 1 edge(s) on 1 document(s)" in text
    assert "`file:docs/page.html` — ref → `file:docs/target.md`" in text
    payload = json.loads(_run(tmp_path, "inspect", "--diff", str(before), str(after), "--json").stdout)
    assert payload["edge_loss"] == 1


def test_the_diff_writes_nothing(tmp_path):
    """Two files in, stdout out. Not even the runtime cache."""
    rows = [{"id": "file:a.md", "edges": []}]
    a = tmp_path / "a.json"
    a.write_text(json.dumps({"corpus": {}, "documents": rows}), encoding="utf-8")
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    _run(tmp_path, "inspect", "--diff", str(a), str(a))
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")) == before
