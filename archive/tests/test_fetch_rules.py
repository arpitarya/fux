"""Tests for fux.fetchrules — text extraction from URL / file / PDF."""
from __future__ import annotations

import http.server
import textwrap
import threading
from pathlib import Path

import pytest

from fux import fetchrules
from fux.errors import FuxError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serve_once(content: bytes, content_type: str = "text/html; charset=utf-8"):
    """Spin up a one-shot HTTP server on localhost and return its URL."""
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(content)
        def log_message(self, *_):
            pass  # silence

    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.handle_request, daemon=True)
    t.start()
    return f"http://127.0.0.1:{port}/"


# ---------------------------------------------------------------------------
# source_label
# ---------------------------------------------------------------------------

def test_source_label_url():
    assert fetchrules.source_label("https://example.com/guide.html") == "https://example.com/guide.html"


def test_source_label_file(tmp_path):
    p = tmp_path / "style-guide.md"
    p.touch()
    assert fetchrules.source_label(str(p)) == "style-guide.md"


# ---------------------------------------------------------------------------
# Local text / markdown files
# ---------------------------------------------------------------------------

def test_read_plain_text_file(tmp_path):
    src = tmp_path / "rules.txt"
    src.write_text("Rule 1: do X.\nRule 2: do Y.\n", encoding="utf-8")
    text = fetchrules.fetch_text(str(src))
    assert "Rule 1" in text
    assert "Rule 2" in text


def test_read_markdown_file(tmp_path):
    src = tmp_path / "guide.md"
    src.write_text("# Style Guide\n\n- Use snake_case\n", encoding="utf-8")
    text = fetchrules.fetch_text(str(src))
    assert "snake_case" in text


def test_missing_file_raises(tmp_path):
    with pytest.raises(fetchrules.FetchError, match="path not found"):
        fetchrules.fetch_text(str(tmp_path / "nonexistent.txt"))


# ---------------------------------------------------------------------------
# HTML stripping
# ---------------------------------------------------------------------------

def test_strip_html_removes_tags():
    raw = "<html><head><title>T</title></head><body><p>Hello <b>world</b></p></body></html>"
    result = fetchrules._strip_html(raw)
    assert "Hello" in result
    assert "world" in result
    assert "<" not in result


def test_strip_html_removes_script_and_style():
    raw = "<html><body><script>alert(1)</script><style>.x{color:red}</style><p>Keep me</p></body></html>"
    result = fetchrules._strip_html(raw)
    assert "alert" not in result
    assert "color" not in result
    assert "Keep me" in result


def test_strip_html_decodes_entities():
    raw = "<p>AT&amp;T &lt;ticker&gt;</p>"
    result = fetchrules._strip_html(raw)
    assert "AT&T" in result
    assert "<ticker>" in result


def test_strip_html_collapses_whitespace():
    raw = "<p>  too    many   spaces  </p>"
    result = fetchrules._strip_html(raw)
    assert "  " not in result


# ---------------------------------------------------------------------------
# URL fetching (local server)
# ---------------------------------------------------------------------------

def test_fetch_plain_text_url():
    body = b"Rule: always validate input.\nFormula: tax = rate * base.\n"
    url = _serve_once(body, "text/plain; charset=utf-8")
    text = fetchrules.fetch_text(url)
    assert "validate input" in text
    assert "tax = rate" in text


def test_fetch_html_url_strips_tags():
    body = b"<html><body><h1>Guide</h1><p>Use ISO dates.</p></body></html>"
    url = _serve_once(body, "text/html; charset=utf-8")
    text = fetchrules.fetch_text(url)
    assert "ISO dates" in text
    assert "<" not in text


def test_fetch_url_bad_host_raises():
    with pytest.raises(fetchrules.FetchError):
        fetchrules.fetch_text("http://localhost:1/")  # nothing listening


# ---------------------------------------------------------------------------
# PDF — dependency missing path
# ---------------------------------------------------------------------------

def test_pdf_without_pypdf_raises(tmp_path, monkeypatch):
    # Simulate pypdf not being installed
    import builtins
    real_import = builtins.__import__
    def fake_import(name, *args, **kwargs):
        if name == "pypdf":
            raise ImportError("No module named 'pypdf'")
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF-1.4 fake")
    with pytest.raises(fetchrules.PDFDependencyError):
        fetchrules.fetch_text(str(src))


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------

def test_cli_fetch_rules_text_file(tmp_path, capsys):
    src = tmp_path / "policy.txt"
    src.write_text("Capital gains on equity: 20%.\n", encoding="utf-8")

    from fux.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["fetch-rules", str(src)])
    rc = args.fn(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Capital gains" in out
    assert "Source:" in out  # header line present by default


def test_cli_fetch_rules_raw_flag(tmp_path, capsys):
    src = tmp_path / "policy.txt"
    src.write_text("Rule: never hardcode secrets.\n", encoding="utf-8")

    from fux.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["fetch-rules", "--raw", str(src)])
    rc = args.fn(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Source:" not in out
    assert "never hardcode secrets" in out


def test_cli_fetch_rules_missing_file(tmp_path, capsys):
    from fux.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["fetch-rules", str(tmp_path / "nope.txt")])
    # A missing source is an expected failure → FuxError (terse `error:` on stderr
    # at the CLI boundary), not a stdout/stderr print + return 1.
    with pytest.raises(FuxError, match="path not found"):
        args.fn(args)
