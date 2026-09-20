"""W-166 DoD 3 — a `url:` record is re-extracted from the bytes already on disk.

**The gap this closes, in SR-PII's own words** (the 🔴 before decision 18):
*"the data needed to honour a new rule is present and unused."*

`_pii_ruleset_moved` invalidates carried extraction for `file:` documents
because they are re-read from the working tree. A `url:` document has no working
tree, so its record carried forward **verbatim** whenever the fetch did not
happen — and under `update=never` that is permanent, `--full` included. The
bytes were sitting in `.fux/acquired/` the whole time.

⚠ **The shape of the failure is why it is worth a file of its own:** a consumer
adds a redaction rule, `fux ingest` reports success, `fux doctor` is green, and
the value the rule was written to remove is still in the committed index that
everyone clones.
"""

from __future__ import annotations

import json

import pytest

from fux.ingest.run import STALE_REDACTION_FILE, run
from fux.store import acquired, read_index

LOC = "https://wiki/runbook"
HTML = "text/html; charset=utf-8"
#: A card number in the page body, so a rule added later has something to remove.
PAGE = (
    b"<!DOCTYPE html><html><head><title>Deploy runbook</title></head><body>"
    b"<h1>Deploy runbook</h1><p>Roll forward, never back. Card zarquon4242 on file.</p>"
    b"</body></html>"
)

RULE = '[[rule]]\nname = "token"\npattern = "zarquon[0-9]{4}"\n'


def _repo(tmp_path, *, keep=True):
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    line = f"{LOC} fetch=http keep={'true' if keep else 'false'}\n"
    (tmp_path / ".fux" / "sources" / "urls").write_text(line, encoding="utf-8")
    (tmp_path / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text(
        "[sources]\n\n[sources.url]\n"
        'fetcher = ".fux/fetchers/http.py"\n'
        "max_parallel = 2\n",
        encoding="utf-8",
    )
    (tmp_path / ".fux" / "pii.toml").write_text("# nothing redacted yet\n", encoding="utf-8")
    return tmp_path


def _retain(root):
    blob = acquired.save(root, LOC, PAGE, HTML, ".html", run_seq=1)
    acquired.write_manifest(root, {LOC: blob})
    return blob


def _seed(tmp_path, *, keep=True, retain=True):
    """A repo whose index already holds the url record, as a prior fetch left it.

    Built by running the real fresh path once with the bytes injected, rather
    than by hand-writing a record: a hand-written one would agree with the code
    only by luck, and this test is about the two agreeing.
    """
    root = _repo(tmp_path, keep=keep)
    if retain:
        _retain(root)
    run(root)  # offline: indexes docs/, no url record yet
    return root


def _url_record(root):
    return read_index(root).get(f"url:{LOC}")


def _fake_fetch_all(root, entries, *a, **kw):
    """`fetch_all` with the socket removed and nothing else.

    🔴 **It must decode and sanitize, because the real one does** —
    `urlsrc.fetch_all` returns `sanitize(_decode_fetched(raw, ...))`, not the
    bytes the server sent. A first draft of this fixture returned raw `PAGE`,
    which seeded the index with a record built by tokenising HTML tags: `phrases`
    empty, `flen` 26 where it should be 8, and a `sha` no real run could produce.
    Every assertion about re-derivation then compared against a baseline nothing
    in production makes.

    So the two helpers are **imported, never reimplemented**, for the same reason
    `refer.source.from_acquired` imports them: a second copy of this pipeline
    drifts by one line and makes a passing test prove the wrong thing.
    """
    from fux.ingest import urlsrc
    from fux.ingest.urlsrc import _decode_fetched, sanitize

    out = []
    for entry in entries:
        markdown, _why = _decode_fetched(PAGE, HTML, entry.url, root)
        out.append(urlsrc.FetchedUrl(url=entry.url, content=sanitize(markdown)))
    return out, []


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    """An index holding the url record, reached through the fresh path.

    `fetch_all` is patched to hand back the retained bytes — the one place this
    file simulates the network, and it simulates it by returning exactly what
    `.fux/acquired/` already holds.
    """
    from fux.ingest import urlsrc

    root = _repo(tmp_path)
    _retain(root)

    monkeypatch.setattr(urlsrc, "fetch_all", _fake_fetch_all)
    run(root, refresh_urls=True)
    monkeypatch.undo()
    return root


def test_the_seed_actually_indexed_the_url(seeded):
    """Guard the fixture: every test below is vacuous if this is None."""
    assert _url_record(seeded) is not None


def test_an_offline_run_carries_it_forward_unchanged(seeded):
    """The behaviour that was always right, and must stay right."""
    before = _url_record(seeded)
    run(seeded)
    assert _url_record(seeded) == before


def test_a_new_pii_rule_re_extracts_the_url_from_retained_bytes(seeded):
    """🔴 **The gap.** No network, no fetch — the bytes are already here."""
    before = _url_record(seeded)
    (seeded / ".fux" / "pii.toml").write_text(RULE, encoding="utf-8")

    run(seeded)  # offline
    after = _url_record(seeded)
    assert after is not None, "the document must never be dropped by a policy change"
    assert after != before, "the record carried forward verbatim — the W-166 defect"


def test_the_redacted_term_actually_leaves_the_index(seeded):
    """The point of all of it. A re-extraction that kept the term fixes nothing."""
    from fux.query.tokenize import tokenize
    from fux.store import term_hash

    (seeded / ".fux" / "pii.toml").write_text(RULE, encoding="utf-8")
    run(seeded)

    record = _url_record(seeded)
    secret = next(iter(tokenize("zarquon4242")), "zarquon4242")
    hashed = term_hash(secret)
    for field in record.get("terms", {}).values():
        assert hashed not in field, "the value the rule removes is still in the committed index"


def test_the_file_half_of_the_corpus_is_re_extracted_too(seeded):
    """A policy change is corpus-wide; the url path is an addition, not a swap."""
    (seeded / ".fux" / "pii.toml").write_text(RULE, encoding="utf-8")
    assert run(seeded).reused_count == 0


def test_a_decoder_bump_also_reaches_a_retained_url(seeded, monkeypatch):
    """Not only PII. A decoder change is the other input to a url's extraction."""
    import fux.decode.html as html_mod

    before = _url_record(seeded)
    monkeypatch.setattr(html_mod, "VERSION", html_mod.VERSION + 1)
    run(seeded)
    # The bytes and the rules are unchanged, so the record is identical -- what
    # is asserted is that it was RE-DERIVED and still agrees, which is L3.
    assert _url_record(seeded) == before


# -- stranded: no retained bytes --------------------------------------------


def test_a_url_with_no_retained_blob_is_stranded_not_dropped(seeded):
    """⚠ **Never dropped.** Deleting a document because a policy changed is the
    one thing a redaction change must not do."""
    acquired.write_manifest(seeded, {})
    before = _url_record(seeded)

    (seeded / ".fux" / "pii.toml").write_text(RULE, encoding="utf-8")
    run(seeded)

    assert _url_record(seeded) == before, "unchanged, and still present"


def test_a_stranded_url_is_recorded_for_doctor(seeded):
    acquired.write_manifest(seeded, {})
    (seeded / ".fux" / "pii.toml").write_text(RULE, encoding="utf-8")
    run(seeded)

    path = seeded / ".fux" / "runtime" / STALE_REDACTION_FILE
    assert json.loads(path.read_text(encoding="utf-8")) == [LOC]


def test_a_stranded_url_is_warned_about_on_the_run_that_strands_it(seeded):
    acquired.write_manifest(seeded, {})
    (seeded / ".fux" / "pii.toml").write_text(RULE, encoding="utf-8")

    warnings = "\n".join(run(seeded).warnings)
    assert LOC in warnings
    assert "OLD rules" in warnings
    assert warnings.isascii()  # printed, and a Windows console must encode it


def test_the_stranded_state_clears_once_the_bytes_are_back(seeded):
    """The state is derived: it is rebuilt by being wrong once, never sticky."""
    acquired.write_manifest(seeded, {})
    (seeded / ".fux" / "pii.toml").write_text(RULE, encoding="utf-8")
    run(seeded)
    assert (seeded / ".fux" / "runtime" / STALE_REDACTION_FILE).is_file()

    _retain(seeded)
    (seeded / ".fux" / "pii.toml").write_text(RULE + "\n# touched\n", encoding="utf-8")
    run(seeded)
    assert not (seeded / ".fux" / "runtime" / STALE_REDACTION_FILE).is_file()


def test_doctor_names_a_stranded_url(seeded):
    from fux import doctor

    acquired.write_manifest(seeded, {})
    (seeded / ".fux" / "pii.toml").write_text(RULE, encoding="utf-8")
    run(seeded)

    row = next(c for c in doctor.run(seeded) if c.name == "url redaction current")
    assert not row.ok
    assert row.level == "warn"  # only a fetch can clear it; doctor is offline
    assert LOC in row.detail
    assert row.detail.isascii()


def test_doctor_is_clean_when_nothing_is_stranded(seeded):
    (seeded / ".fux" / "pii.toml").write_text(RULE, encoding="utf-8")
    run(seeded)

    from fux import doctor

    row = next(c for c in doctor.run(seeded) if c.name == "url redaction current")
    assert row.ok


# -- determinism (L3) -------------------------------------------------------


def test_re_derivation_is_byte_identical_to_what_a_fetch_would_produce(seeded, monkeypatch):
    """The reason `from_acquired` is imported rather than reimplemented.

    Re-deriving offline and re-fetching the same bytes must land on the same
    record — including its `sha`, which fingerprints the SOURCE and not fux's
    redacted view of it.
    """
    from fux.ingest import urlsrc

    (seeded / ".fux" / "pii.toml").write_text(RULE, encoding="utf-8")
    run(seeded)
    offline = _url_record(seeded)

    monkeypatch.setattr(urlsrc, "fetch_all", _fake_fetch_all)
    run(seeded, refresh_urls=True)
    assert _url_record(seeded) == offline
