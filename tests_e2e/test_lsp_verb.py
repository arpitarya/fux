"""`fux lsp` and `fux llms` as a user — and an editor — runs them (W-284, W-285, W-286).

⚠ **Named `test_lsp_verb.py`**, not `test_lsp.py`: the unit suite has that
basename, and two modules sharing one make `pytest tests tests_e2e` fail at
collection (`test_serve_verb.py` carries the same note).

**What this adds over `tests/test_lsp.py`.** That suite drives `Server` in
process. This one starts the real verb, and then drives it with **the VS Code
extension's own client** (`vscode/src/client.js`) under Node — so the two
halves the extension ships are proven to speak to each other, not each to a
fake of the other.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from l12_fixtures import write_config

ROOT = Path(__file__).resolve().parents[1]
DOCS = {
    "ranking.md": "# Ranking\n\n## Saturation\n\nSaturation and length normalisation decide how a "
    "long document is priced.\n\nSee [the walk](walk.md).\n",
    "walk.md": "---\ndescription: \"The personalised walk.\"\n---\n\n# The walk\n\nA personalised "
    "page-rank over committed edges.\n",
}


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    fux = tmp_path / ".fux"
    (fux / "sources").mkdir(parents=True)
    (fux / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (fux / "pii.toml").write_text("", encoding="utf-8")
    write_config(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    for name, body in DOCS.items():
        (docs / name).write_text(body, encoding="utf-8")
    subprocess.run([sys.executable, "-m", "fux.cli", "ingest"], cwd=tmp_path,
                   capture_output=True, text=True, check=True)
    return tmp_path


def _frame(message: dict) -> bytes:
    body = json.dumps(message).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def _read_all(raw: bytes) -> list[dict]:
    out = []
    while raw:
        head, _, rest = raw.partition(b"\r\n\r\n")
        length = int(head.split(b":")[1])
        out.append(json.loads(rest[:length]))
        raw = rest[length:]
    return out


def test_the_lsp_verb_answers_a_whole_session(corpus):
    uri = (corpus / "docs" / "walk.md").as_uri()
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"rootUri": corpus.as_uri()}},
        {"jsonrpc": "2.0", "method": "initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "workspace/symbol", "params": {"query": "saturation"}},
        {"jsonrpc": "2.0", "id": 3, "method": "textDocument/references",
         "params": {"textDocument": {"uri": uri}, "position": {"line": 0, "character": 0}}},
        {"jsonrpc": "2.0", "id": 4, "method": "shutdown"},
        {"jsonrpc": "2.0", "method": "exit"},
    ]
    proc = subprocess.run([sys.executable, "-m", "fux.cli", "lsp"], cwd=corpus,
                          input=b"".join(map(_frame, messages)), capture_output=True, timeout=60)
    assert proc.returncode == 0, proc.stderr.decode()
    replies = {r["id"]: r for r in _read_all(proc.stdout) if "id" in r}
    assert replies[1]["result"]["serverInfo"]["name"] == "fux"
    (symbol,) = [s for s in replies[2]["result"] if s["containerName"] == "docs/ranking.md"]
    assert symbol["location"]["range"]["start"]["line"] == 2
    (ref,) = replies[3]["result"]
    assert ref["uri"].endswith("docs/ranking.md") and ref["range"]["start"]["line"] == 6


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_the_extensions_client_drives_the_real_server(corpus):
    script = f"""
const {{ LspClient }} = require({json.dumps(str(ROOT / "vscode" / "src" / "client.js"))});
(async () => {{
  const c = LspClient.spawn({json.dumps(sys.executable)}, ["-m", "fux.cli", "lsp"], {json.dumps(str(corpus))});
  const init = await c.start({json.dumps(corpus.as_uri())}, {{ name: "e2e" }});
  const symbols = await c.request("workspace/symbol", {{ query: "personalised walk" }});
  await c.stop();
  console.log(JSON.stringify({{ caps: init.capabilities, names: symbols.map((s) => s.containerName) }}));
}})().catch((e) => {{ console.error(e); process.exit(1); }});
"""
    proc = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    got = json.loads(proc.stdout.strip().splitlines()[-1])
    assert got["caps"]["workspaceSymbolProvider"] is True
    assert got["names"][0] == "docs/walk.md"


def test_the_llms_verb_prints_an_llms_txt(corpus):
    out = subprocess.run([sys.executable, "-m", "fux.cli", "llms", "--title", "Demo", "--full"],
                         cwd=corpus, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    assert out.startswith("# Demo\n\n## docs\n\n- [Ranking](docs/ranking.md)\n"
                          "- [The walk](docs/walk.md): The personalised walk.\n")
    assert "Source: docs/walk.md\n\n# The walk\n" in out
    assert "description:" not in out
