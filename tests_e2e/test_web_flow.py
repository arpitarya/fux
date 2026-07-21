"""Web ingestion e2e against a local stdlib http.server — never the real internet."""

from __future__ import annotations

import http.server
import json
import shutil
import threading
from pathlib import Path

import pytest

from conftest import E2E_DIR, fux_tree, run_fux

SITE = E2E_DIR / "site"


@pytest.fixture
def web_project(tmp_path):
    """A project whose [sources.web] points at a served copy of tests_e2e/site."""
    served = tmp_path / "served"
    shutil.copytree(SITE, served)
    (served / "big.pdf").write_bytes(b"%PDF-1.4 " + b"\0" * (200 * 1024))
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=str(served), **kw
    )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "docs").mkdir()
    (proj / "docs/local.md").write_text("# Local\n\nA local doc lives here.\n", encoding="utf-8")
    (proj / "fux.toml").write_text(
        "[sources]\n"
        'docs = ["docs"]\n'
        "[sources.web]\n"
        f'urls = ["{base}/index.html"]\n'
        "max_depth = 1\n"
        "delay_s = 0.0\n"
        "max_fetch_kb = 64\n"
        'attachments = ["pdf", "png"]\n',
        encoding="utf-8",
    )
    yield proj, base
    server.shutdown()


def hosted(base: str) -> str:
    return base.replace("http://", "").replace(":", "_")


def test_crawl_flow_provenance_and_robots(web_project):
    proj, base = web_project
    out = run_fux(proj, "ingest", "--web").stdout
    assert "web" in out

    manifest = {
        json.loads(line)["source"]: json.loads(line)
        for line in (proj / ".fux/manifest.jsonl").read_text(encoding="utf-8").splitlines()
    }
    index_entry = manifest[f"{base}/index.html"]
    assert index_entry["origin"] == "url" and index_entry["depth"] == 0
    page2 = manifest[f"{base}/page2.html"]
    assert page2["parent"] == f"{base}/index.html" and page2["depth"] == 1
    png = manifest[f"{base}/logo.png"]
    assert png["origin"] == "attachment" and png["kind"] == "image"

    # robots-disallowed and oversize and offsite never entered the corpus
    assert not any("secret" in s for s in manifest)
    assert not any("big.pdf" in s for s in manifest)
    assert not any("offsite" in s for s in manifest)

    skips = run_fux(proj, "ingest", "--list-skipped").stdout
    assert "disallowed by robots.txt" in skips
    assert "larger than max_fetch_kb" in skips
    assert "off-domain" in skips

    cache = proj / f".fux/cache/_web/{hosted(base)}/index.html.md"
    assert cache.is_file()
    text = cache.read_text(encoding="utf-8")
    assert "origin: url" in text and f"url: {base}/index.html" in text
    assert "The exporter batches telemetry" in text


def test_web_citations_show_urls(web_project):
    proj, base = web_project
    run_fux(proj, "ingest", "--web")
    out = run_fux(proj, "ask", "how often does the exporter batch telemetry", "--json").stdout
    top = json.loads(out)["results"][0]
    assert top["path"] == f"{base}/index.html"
    assert top["line_start"] is None  # synthetic conversion: no fabricated lines

    human = run_fux(proj, "answer", "how often does the exporter batch telemetry").stdout
    assert f"[1] {base}/index.html" in human


def test_recrawl_unchanged_is_byte_identical(web_project):
    proj, base = web_project
    run_fux(proj, "ingest", "--web")
    first = fux_tree(proj)
    run_fux(proj, "ingest", "--web")
    assert fux_tree(proj) == first


def test_local_only_ingest_preserves_web_entries_and_check_ignores_them(web_project):
    proj, base = web_project
    run_fux(proj, "ingest", "--web")
    run_fux(proj, "ingest")  # local-only refresh
    manifest = (proj / ".fux/manifest.jsonl").read_text(encoding="utf-8")
    assert f"{base}/index.html" in manifest
    proc = run_fux(proj, "ingest", "--check")
    assert "cache is fresh" in proc.stdout  # web origins excluded from drift
