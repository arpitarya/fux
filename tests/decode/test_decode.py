"""The decoder plane — protocol, dispatch, override, and the invariants that
make it safe to put consumer code on the ingest path (W-86 P1).

The tests that matter most here are not the happy paths. They are:
  * the fetchers agree with the built-in *by construction* now, not by comment;
  * a missing consumer dependency FAILS rather than silently shrinking the index;
  * a malformed document is a skipped document, never a failed ingest.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from fux import decode as decode_mod
from fux.decode import claims, decode, registry
from fux.decode.htmldoc import html_to_markdown
from fux.errors import FuxError
from fux.ingest.parse import parse_document

HTML = b"""<!doctype html>
<html><head><title>Runbook</title><style>b{}</style></head>
<body>
<h1>Restarting the broker</h1>
<p>Drain the queue <b>first</b>.</p>
<ul><li>stop consumers</li><li>flush</li></ul>
<table><tr><th>step</th><th>owner</th></tr><tr><td>drain</td><td>sre</td></tr></table>
<pre>systemctl stop broker</pre>
</body></html>
"""


# -- protocol + dispatch ----------------------------------------------------


def test_html_is_claimed_and_markdown_comes_out():
    assert claims("docs/runbook.html")
    out = decode(HTML, "docs/runbook.html")
    assert out is not None
    assert "# Restarting the broker" in out
    assert "- stop consumers" in out
    assert "| step | owner |" in out
    assert "```" in out


def test_unclaimed_extension_returns_none_rather_than_guessing():
    # `.md` is already prose; the decoder plane must not touch it, or every
    # markdown document in every corpus would be round-tripped through a parser.
    assert not claims("README.md")
    assert decode(b"# hi", "README.md") is None


def test_extension_match_is_case_insensitive():
    # A case-insensitive checkout can hand back `PAGE.HTML` for a file committed
    # as `page.html`. A registry keyed on raw case would make the index depend
    # on which machine cloned the repo.
    assert claims("PAGE.HTML")
    assert claims("page.HtMl")


def test_a_dotfile_with_no_extension_is_not_a_format():
    assert not claims(".gitignore")
    assert not claims("Makefile")


def test_empty_output_reads_as_none_not_as_an_empty_document():
    # A page of nothing but chrome has no prose. Indexing it as a zero-term
    # document would put an empty record in the index and distort `df`.
    assert decode(b"<html><body><style>x{}</style></body></html>", "a.html") is None


# -- determinism (L3) -------------------------------------------------------


def test_decoding_is_byte_identical_across_processes():
    """Same bytes -> same string, in a fresh interpreter with a different hash
    seed. Dict and set iteration order is the usual way a decoder becomes
    accidentally environment-dependent, and PYTHONHASHSEED is how that shows up.
    """
    script = textwrap.dedent(
        """
        import sys, hashlib
        from fux.decode import decode
        raw = sys.stdin.buffer.read()
        out = decode(raw, "x.html")
        sys.stdout.write(hashlib.sha256(out.encode()).hexdigest())
        """
    )
    digests = set()
    for seed in ("0", "1", "12345"):
        # The parent environment is inherited and only the seed overridden. A
        # hand-built minimal env looks tidier and silently breaks the moment a
        # decoder needs anything the harness set up — which is a test failing
        # for a reason that has nothing to do with determinism.
        env = dict(os.environ, PYTHONHASHSEED=seed)
        env["PYTHONPATH"] = os.pathsep.join(
            p for p in (_src(), env.get("PYTHONPATH", "")) if p
        )
        result = subprocess.run(
            [sys.executable, "-c", script], input=HTML, capture_output=True, env=env
        )
        assert result.returncode == 0, result.stderr.decode()[-2000:]
        digests.add(result.stdout.decode())
    assert len(digests) == 1, "decoding varied with hash seed"


def _src() -> str:
    return str(Path(__file__).resolve().parents[2] / "src")


# -- the reason this module exists: the fetchers agreed only by comment ------


def test_both_fetchers_now_share_one_conversion():
    """`http.py` and `cdp.py` each carried a hand-maintained `_MdParser`, with a
    docstring asking them to stay identical and nothing enforcing it. Which
    fetcher retrieved a URL was therefore a property of the committed index.
    Assert the copies are gone, not merely that they currently agree.
    """
    root = Path(__file__).resolve().parents[2]
    for name in ("http.py", "cdp.py"):
        source = (root / ".fux" / "fetchers" / name).read_text()
        assert "class _MdParser" not in source, f"{name} still carries a copy of the parser"
        # W-86 P8 went further than P1: a fetcher no longer converts at all, so
        # it does not even import the converter. `fetch()` returns bytes and the
        # decoder plane runs afterwards — agreement by construction, not by
        # sharing an import.
        assert "html_to_markdown" not in source, f"{name} still converts"
        assert "-> tuple[bytes, str]" in source, f"{name} does not return bytes + type"


def test_the_shared_conversion_is_the_one_the_fetchers_call():
    assert "# Restarting the broker" in html_to_markdown(HTML.decode())


# -- consumer decoders ------------------------------------------------------


def _write_consumer(root: Path, name: str, body: str) -> None:
    directory = root / ".fux" / "decoders"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{name}.py").write_text(textwrap.dedent(body))


def test_a_consumer_decoder_adds_a_new_format(tmp_path):
    _write_consumer(
        tmp_path,
        "logdoc",
        """
        EXTENSIONS = (".log",)

        def decode(raw, rel_path):
            return "# log\\n\\n" + raw.decode()
        """,
    )
    assert claims("app.log", tmp_path)
    assert decode(b"boom", "app.log", tmp_path) == "# log\n\nboom"


def test_a_consumer_decoder_overrides_the_builtin_by_module_name(tmp_path):
    _write_consumer(
        tmp_path,
        "htmldoc",
        """
        EXTENSIONS = (".html",)

        def decode(raw, rel_path):
            return "# replaced"
        """,
    )
    assert decode(HTML, "x.html", tmp_path) == "# replaced"
    # And the built-in is not consulted at all — not merged, not fallen back to.
    assert registry(tmp_path)[".html"].name == "htmldoc"
    assert registry(tmp_path)[".html"].origin.endswith("htmldoc.py")


def test_underscore_files_are_helpers_not_decoders(tmp_path):
    _write_consumer(tmp_path, "_shared", "EXTENSIONS = ('.zzz',)\ndef decode(raw, rel_path): return 'x'\n")
    assert not claims("a.zzz", tmp_path)


def test_a_missing_dependency_fails_loudly_and_names_it(tmp_path):
    """Arpit's ruling, 2026-08-26: unless the consumer adds the dependency the
    feature is unavailable — and *unavailable* has to mean an error, not a
    smaller index. Two machines with the same sources must not commit different
    indexes because one of them had a library installed.
    """
    _write_consumer(
        tmp_path,
        "pdfdoc",
        """
        import a_library_nobody_has

        EXTENSIONS = (".pdf",)

        def decode(raw, rel_path):
            return "never reached"
        """,
    )
    with pytest.raises(FuxError) as exc:
        registry(tmp_path)
    message = str(exc.value)
    assert "a_library_nobody_has" in message
    assert "install" in message.lower()
    assert "different index" in message


def test_a_consumer_decoder_may_ask_for_a_path(tmp_path):
    """The opt-in half of the protocol. Libraries like pypdf and olefile want a
    real file rather than a buffer; without this every such decoder would spill
    its own temp file, fifteen slightly different ways.
    """
    _write_consumer(
        tmp_path,
        "pathdoc",
        """
        WANTS_PATH = True
        EXTENSIONS = (".bin",)

        def decode(path, rel_path):
            assert path.is_file(), "fux promised a real file"
            assert path.suffix == ".bin", "the suffix is kept for sniffing"
            return "# " + path.read_bytes().decode()
        """,
    )
    assert decode(b"payload", "x.bin", tmp_path) == "# payload"


def test_the_temp_file_does_not_survive_the_call(tmp_path):
    seen = tmp_path / "seen.txt"
    _write_consumer(
        tmp_path,
        "leakdoc",
        f"""
        WANTS_PATH = True
        EXTENSIONS = (".leak",)

        def decode(path, rel_path):
            open({str(seen)!r}, "w").write(str(path))
            return "# ok"
        """,
    )
    decode(b"x", "a.leak", tmp_path)
    assert not Path(seen.read_text()).exists()


def test_a_consumer_file_that_is_not_a_decoder_says_so(tmp_path):
    _write_consumer(tmp_path, "notadecoder", "VALUE = 1\n")
    with pytest.raises(FuxError, match="defines no EXTENSIONS"):
        registry(tmp_path)


# -- malformed input is data, not a bug -------------------------------------


def test_a_decoder_that_explodes_skips_the_document_instead_of_the_run(tmp_path):
    _write_consumer(
        tmp_path,
        "boomdoc",
        """
        EXTENSIONS = (".boom",)

        def decode(raw, rel_path):
            raise ValueError("truncated")
        """,
    )
    with pytest.raises(decode_mod.DecodeFailed):
        decode(b"x", "a.boom", tmp_path)
    # ...and at the ingest seam that becomes a skipped document, not a crash.
    assert parse_document(b"x", "a.boom", tmp_path) is None


def test_decode_failed_is_not_a_fuxerror():
    """`FuxError` is rendered at the CLI boundary as *the command failed*. One
    unreadable file among ten thousand is not that, so the two must not share a
    type or a corrupt PDF would end an ingest.
    """
    assert not issubclass(decode_mod.DecodeFailed, FuxError)


# -- the ingest seam --------------------------------------------------------


def test_parse_document_leaves_prose_untouched():
    doc = parse_document(b"---\ntitle: x\n---\n\n# Body\n", "a.md")
    assert doc is not None
    assert doc.meta == {"title": "x"}
    assert doc.body.strip() == "# Body"


def test_decoded_output_is_not_re_read_as_frontmatter():
    """An `<hr>` converts to `---`. If the frontmatter parser ran over decoded
    Markdown it would swallow that as a delimiter and eat the document's head.
    """
    doc = parse_document(b"<html><body><hr><p>real content here</p></body></html>", "a.html")
    assert doc is not None
    assert doc.meta == {}
    assert "real content here" in doc.body


def test_an_undecodable_claimed_file_is_a_skip_not_a_fallback(tmp_path):
    # Without this, a decoder returning None would fall through to the prose
    # path and index the raw bytes of a binary file as if they were text.
    _write_consumer(
        tmp_path,
        "nulldoc",
        """
        EXTENSIONS = (".nul",)

        def decode(raw, rel_path):
            return None
        """,
    )
    assert parse_document(b"some bytes", "a.nul", tmp_path) is None
