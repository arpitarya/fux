"""`fux serve`'s X-ray tabs (W-220): the routes answer from `fux.inspect`,
in-process, and write nothing but the gitignored cache.

[SR-SERVE](../../records/0158_serve.md) decisions 4, 5 and 15. The page's side —
that the browser computes nothing — is `test_page_computes_nothing.py`'s.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from fux.inspect import as_dict, inspect_index
from fux.serve import HOST, make_server

DOCS = {
    "ranking.md": "# Ranking\n\nSaturation and length normalisation decide how a long "
    "document is priced.\n\nSee [the walk](walk.md).\n",
    "walk.md": "# The walk\n\nA personalised page-rank over committed edges.\n",
    "fetching.md": "# Fetching\n\nAcquisition, digests and verification at answer time.\n",
}


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("serve-xray")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    fux = root / ".fux"
    (fux / "sources").mkdir(parents=True)
    (fux / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (fux / "pii.toml").write_text("", encoding="utf-8")
    docs = root / "docs"
    docs.mkdir()
    for name, body in DOCS.items():
        (docs / name).write_text(body, encoding="utf-8")
    subprocess.run([sys.executable, "-m", "fux.cli", "ingest"], cwd=root,
                   capture_output=True, text=True, check=True)
    return root


@pytest.fixture
def server(corpus):
    srv = make_server(port=0, root=corpus)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{HOST}:{srv.server_address[1]}"
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=5)


def get(base: str, path: str):
    try:
        with urllib.request.urlopen(base + path, timeout=60) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def wait(base: str, path: str) -> dict:
    """Poll a job route until it is done. A test clock, never the page's."""
    for _ in range(600):
        status, payload = get(base, path)
        assert status == 200, payload
        if payload["state"] == "done":
            return payload["report"]
        assert payload["state"] == "running", payload
        time.sleep(0.05)
    raise AssertionError(f"{path} never finished")


def test_documents_lists_the_register(server, corpus):
    status, payload = get(server, "/inspect/documents")
    assert status == 200
    assert [row["loc"] for row in payload["documents"]] == [
        "docs/fetching.md", "docs/ranking.md", "docs/walk.md",
    ]
    assert payload["count"] == 3


def test_one_document_is_xrayed_on_the_click(server):
    status, x = get(server, "/inspect/document?loc=docs/ranking.md")
    assert status == 200
    assert x["loc"] == "docs/ranking.md"
    assert x["ingested"]["passages"] >= 1
    assert [link["id"] for link in x["links"]["out"]] == ["file:docs/walk.md"]


def test_a_documents_probes_are_its_title_and_headings(server):
    status, payload = get(server, "/inspect/document/probes?loc=docs/walk.md")
    assert status == 200
    assert payload["probe"]["title"] == 1


def test_an_unknown_document_is_a_4xx_with_a_sentence(server):
    status, payload = get(server, "/inspect/document?loc=docs/nope.md")
    assert status == 400 and "no indexed document" in payload["error"]


def test_the_index_tab_is_the_library_report_without_probes(server, corpus):
    """The same numbers `fux inspect --json` prints — one engine, two front doors."""
    report = wait(server, "/inspect/index")
    assert report["probes"] is None
    direct = as_dict(inspect_index(corpus, probe_sample=None, retrieval_sample=None, top=200))
    assert report["checks"] == direct["checks"]
    assert report["documents"] == direct["documents"]


def test_the_probe_job_reports_every_document_on_all(server):
    report = wait(server, "/inspect/probes?all=1")
    assert report["probes"]["sampled"] == 3 and report["probes"]["estimate"] is False


def test_a_reopened_tab_on_an_unchanged_index_recomputes_nothing(server):
    first = wait(server, "/inspect/index")
    status, again = get(server, "/inspect/index")
    assert status == 200 and again["state"] == "done" and again["report"] == first


def _outside_runtime(root: Path) -> dict:
    import hashlib

    out = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_file() and not rel.startswith((".fux/runtime/", ".git/")):
            out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def test_no_route_writes_outside_the_runtime_cache(server, corpus):
    """Decision 4 as amended: the X-ray routes fill `.fux/runtime/inspect/`
    and touch no other byte — not the index, not a source, not the config."""
    before = _outside_runtime(corpus)
    wait(server, "/inspect/probes")
    get(server, "/inspect/document?loc=docs/walk.md")
    get(server, "/inspect/document/probes?loc=docs/walk.md")
    get(server, "/inspect/documents")
    assert _outside_runtime(corpus) == before
    assert (corpus / ".fux" / "runtime" / "inspect" / "facts.json").is_file()


def test_writes_are_still_refused(server):
    request = urllib.request.Request(server + "/inspect/index", method="POST", data=b"")
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(request, timeout=10)
    assert excinfo.value.code == 405
