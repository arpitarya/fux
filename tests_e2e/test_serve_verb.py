"""`fux serve` as a user runs it — a real process, a real socket, a real page.

⚠ **Named `test_serve_verb.py`, not `test_serve.py`.** Neither test tree carries
an `__init__.py`, so two modules sharing a basename make `pytest tests tests_e2e`
fail at **collection** — an error that reads like a broken import and is a file
name. `test_inspect_verb.py` carries the same note for the same reason.

**What this adds over `tests/serve/`.** That suite drives the handler in-process
with the server object in hand. This one does what a person does: starts the
command, waits for the line it prints, fetches from another process, and stops
it with Ctrl-C. It is the only place that proves the verb *starts* — an import
error, a missing `page.html` in the package, or a handler that raises before
`serve_forever` are all invisible to an in-process test that constructs the
server itself.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

DOCS = {
    "ranking.md": "# Ranking\n\nSaturation and length normalisation decide how a long "
    "document is priced against a short one.\n\nSee [the walk](walk.md).\n",
    "walk.md": "# The walk\n\nA personalised page-rank over committed edges promotes a "
    "neighbour of a good answer with no lexical match at all.\n",
}


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    fux = tmp_path / ".fux"
    (fux / "sources").mkdir(parents=True)
    (fux / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (fux / "pii.toml").write_text("", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    for name, body in DOCS.items():
        (docs / name).write_text(body, encoding="utf-8")
    subprocess.run(
        [sys.executable, "-m", "fux.cli", "ingest"],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    return tmp_path


@pytest.fixture
def served(corpus):
    """The verb, started the way a person starts it, and stopped the way they stop it.

    ⚠ **The port is probed rather than fixed.** A hard-coded port in a suite is
    a flake waiting for a busy machine, and it fails as a connection error that
    reads like the feature being broken.
    """
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "fux.cli", "serve", "--port", str(port)],
        cwd=corpus, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    base = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            pytest.fail(f"fux serve exited {proc.returncode}: {proc.stderr.read()}")
        try:
            with urllib.request.urlopen(base + "/health", timeout=1):
                break
        except OSError:
            time.sleep(0.05)
    else:  # pragma: no cover - only on a machine that never came up
        proc.kill()
        pytest.fail("fux serve never answered /health")
    try:
        yield base, proc
    finally:
        if proc.poll() is None:
            proc.send_signal(signal.SIGINT if os.name != "nt" else signal.SIGTERM)
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:  # pragma: no cover
                proc.kill()


def _get(base: str, path: str) -> str:
    with urllib.request.urlopen(base + path, timeout=30) as response:
        return response.read().decode("utf-8")


def test_the_verb_starts_and_serves_its_page(served):
    base, _ = served
    page = _get(base, "/")
    assert "<title>fux — ask explorer</title>" in page
    assert "<script>" in page and "src=" not in page.split("<script>")[0][-200:]


def test_a_user_can_ask_a_question_over_http(served):
    base, _ = served
    payload = json.loads(_get(base, "/ask?q=saturation%20length%20normalisation"))
    assert payload["results"], "the planted document should rank"
    top = payload["derivation"]["documents"][0]
    assert top["matched"], "--why must carry the matched terms the page draws"
    assert any(m["contribution"] is not None for m in top["matched"]), (
        "the page's score-by-word bar reads `contribution`; without it the bar "
        "would have to recompute BM25F in the browser, which is the one thing "
        "this feature refuses"
    )


def test_the_score_decomposition_the_page_prints_actually_reconciles(served):
    """🔴 `score == sum(contribution) * rerank_uplift * multiplier`.

    The page prints that identity as a sentence under every result. If it ever
    stops holding, the page is showing a decomposition of a score that was
    composed some other way — a plausible number beside the real one, which is
    the failure `provenance.py` is written around.
    """
    base, _ = served
    payload = json.loads(_get(base, "/ask?q=saturation%20length%20normalisation"))
    for doc in payload["derivation"]["documents"]:
        contributions = [m["contribution"] for m in doc["matched"]]
        if not contributions or any(c is None for c in contributions):
            continue
        product = sum(contributions) * (doc.get("rerank_uplift") or 1.0) * doc["multiplier"]
        assert product == pytest.approx(doc["score"], rel=1e-9), (
            f"{doc['loc']}: the printed score does not reconcile with its attribution"
        )


def test_the_verb_prints_the_url_it_bound(served):
    base, proc = served
    proc.send_signal(signal.SIGINT if os.name != "nt" else signal.SIGTERM)
    proc.wait(timeout=15)
    out = proc.stdout.read()
    assert base in out, "a person needs the URL, and it has to be the one it actually bound"
    assert "computes nothing" in out, "the one sentence that says what the page is"
