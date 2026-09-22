"""`fux serve`'s four routes, its one bind address, and the promise that makes
the page honest: **`/ask` is byte-identical to the CLI.**

🔴 **The byte-equality test is the load-bearing one.** The whole design of
[`serve/`](../../src/fux/serve/__init__.py) rests on the page being a *renderer*
— nothing in it computes a score, a band or a rank — and that is only true if
the bytes it renders are the ones `fux ask --json --why` prints. A second
payload builder would be a second contract, free to drift a key at a time with
nothing to notice, and the page would quietly start describing a ranking fux did
not do.

The route answers by **running the command**, so this test cannot really fail
for a drift reason — which is the point. What it CAN catch is somebody
"optimising" the route into a direct call on the query API, and that is exactly
the change this file exists to refuse.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

from fux.errors import FuxError
from fux.serve import HOST, PAGE, _bind_address, make_server

DOCS = {
    "ranking.md": "# Ranking\n\nSaturation and length normalisation decide how a "
    "long document is priced against a short one, and the weighted field sum is "
    "resolved at query time.\n\nSee [the walk](walk.md).\n",
    "walk.md": "# The walk\n\nA personalised page-rank over committed edges "
    "promotes a neighbour of a good answer without any lexical match at all.\n",
    "fetching.md": "# Fetching\n\nAcquisition, digests and verification of the "
    "systems that own a document, checked at answer time.\n",
}


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> Path:
    """A three-document repository, ingested once for this module.

    ⚠ **`.fux/pii.toml` must exist or every verb refuses** — `work/MACHINE.md`
    §Two test invocations names a hand-built repo without it as one of the two
    failures that are not failures.
    """
    root = tmp_path_factory.mktemp("serve-corpus")
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    fux = root / ".fux"
    (fux / "sources").mkdir(parents=True)
    (fux / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (fux / "pii.toml").write_text("", encoding="utf-8")
    docs = root / "docs"
    docs.mkdir()
    for name, body in DOCS.items():
        (docs / name).write_text(body, encoding="utf-8")
    subprocess.run(
        [sys.executable, "-m", "fux.cli", "ingest"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    return root


@pytest.fixture
def server(corpus, monkeypatch):
    """A real server on a free port, in this process, rooted at the corpus.

    🔴 **`port=0`, never a fixed one.** A suite that hard-codes a port is a
    flake waiting for a busy machine, and it fails in the least informative way
    available — a connection error that looks like the feature is broken.
    """
    monkeypatch.chdir(corpus)
    srv = make_server(port=0)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{HOST}:{srv.server_address[1]}"
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=5)


def get(base: str, path: str) -> tuple[int, str, str]:
    try:
        with urllib.request.urlopen(base + path, timeout=30) as response:
            return response.status, response.read().decode("utf-8"), response.headers["Content-Type"]
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8"), exc.headers["Content-Type"]


# --- the bind address is the contract, not a default ------------------------


@pytest.mark.parametrize("host", [None, "", HOST, "localhost"])
def test_the_only_addresses_accepted_resolve_to_loopback(host):
    assert _bind_address(host) == HOST


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.168.1.10", "example.com"])
def test_any_other_bind_address_is_refused_by_name(host):
    """🔴 **Not a default that can be overridden — a refusal.**

    The page shows a corpus's vocabulary, its passages, and the questions
    somebody typed. L4 is offline-by-default, and there is no flag that reaches
    this function, so a future `--host` would have to delete the refusal rather
    than pass through it — which is a diff somebody reviews.
    """
    with pytest.raises(FuxError, match="binds 127.0.0.1"):
        _bind_address(host)


# --- the four routes --------------------------------------------------------


def test_the_root_serves_one_self_contained_page(server):
    status, body, content_type = get(server, "/")
    assert status == 200
    assert "text/html" in content_type
    assert body == PAGE.read_text(encoding="utf-8")


def test_health_names_the_engine_and_the_index(server):
    status, body, _ = get(server, "/health")
    assert status == 200
    payload = json.loads(body)
    assert payload["host"] == HOST
    assert payload["schema"].startswith("fux.index.")
    assert payload["version"] and payload["analyzer"]


def test_ask_returns_the_ranked_list_with_its_derivation(server):
    status, body, content_type = get(server, "/ask?q=saturation%20length")
    assert status == 200
    assert "application/json" in content_type
    payload = json.loads(body)
    assert payload["results"], "the planted document should rank"
    assert "derivation" in payload and "confidence" in payload


def test_ask_with_no_question_is_a_named_refusal_not_an_empty_list(server):
    status, body, _ = get(server, "/ask?q=")
    assert status == 400
    assert "question" in json.loads(body)["error"]


@pytest.mark.parametrize("bad", ["0", "-3", "lots"])
def test_a_nonsense_top_is_refused_rather_than_silently_ignored(server, bad):
    status, body, _ = get(server, f"/ask?q=walk&top={bad}")
    assert status == 400
    assert "positive integer" in json.loads(body)["error"]


def test_graph_walks_from_a_named_seed(server):
    status, body, _ = get(server, "/graph?seed=docs/ranking.md")
    assert status == 200
    assert "nodes" in json.loads(body)


def test_graph_without_a_seed_says_which_argument_is_missing(server):
    status, body, _ = get(server, "/graph")
    assert status == 400
    assert "seed" in json.loads(body)["error"]


def test_an_unknown_route_is_a_404_that_names_itself(server):
    status, body, _ = get(server, "/corpus")
    assert status == 404
    assert "/corpus" in json.loads(body)["error"]


# --- no route writes anything -----------------------------------------------


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
def test_every_writing_method_is_refused_with_a_reason(server, method):
    """The page proposes levers and applies none — DoD "out of scope", as code.

    A 405 with a sentence is what tells the next person that read-only is a
    decision rather than an omission somebody should helpfully fill in.
    """
    request = urllib.request.Request(server + "/ask?q=walk", method=method, data=b"")
    with pytest.raises(urllib.error.HTTPError) as caught:
        urllib.request.urlopen(request, timeout=30)
    assert caught.value.code == 405
    assert "read-only" in caught.value.read().decode("utf-8")


# --- the promise the whole design rests on ----------------------------------


@pytest.mark.parametrize("query", ["saturation length", "the walk", "zzz nothing matches this"])
def test_ask_is_byte_identical_to_the_cli(server, corpus, query):
    """🔴 **The route's output IS `fux ask --json --why --band`'s stdout.**

    Byte for byte, including key order, float repr and whitespace — because the
    route runs that command rather than rebuilding its payload. If this ever
    fails, somebody has replaced the command with a call, and the page has
    started rendering a second contract.

    ⚠ **The third query matches nothing on purpose.** The empty-list shape is
    the one a page is most likely to special-case, and it is the one state the
    band exists for.
    """
    _, served, _ = get(server, "/ask?q=" + urllib.parse.quote(query))
    cli = subprocess.run(
        [sys.executable, "-m", "fux.cli", "ask", query, "--json", "--why", "--band"],
        cwd=corpus, capture_output=True, text=True, encoding="utf-8",
    )
    assert served == cli.stdout
