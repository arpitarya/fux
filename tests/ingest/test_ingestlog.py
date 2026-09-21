"""W-200: one runtime line per consumed document, naming what read it.

⚠ **Named `test_ingest_provenance.py`, not `test_provenance.py`.** pytest
imports test modules by basename, and `tests/query/test_provenance.py` already
exists for SR-PROVENANCE's answer receipts — a second file by that name is a
hard collection error, which is the harness telling you the same thing the two
source modules do: **these are opposite subjects that happen to share a word.**

**Arpit, 2026-09-18:** *"Create a log file of the files that are being consumed
as well as the URLs that are being consumed, with what decoders were used, what
version they were used, and just some kind of information."*

Every test here asserts one of the five decisions the module docstring makes,
because each has a cost and a test is where a cost stops being rediscovered:

1. **runtime, never committed** — `test_the_ledger_is_under_the_derived_directory`
2. **clock-free (L3)** — `test_no_row_carries_a_clock`
3. **best-effort** — `test_an_unwritable_ledger_is_a_note_not_a_failure`
4. **its own file** — implied by (1); `docs.jsonl` is untouched
5. **`reused` carries the PRIOR decoder** — `test_a_reused_row_carries_the_decoder_that_made_the_record`,
   which is the one that makes `doctor`'s stale-decoder finding fireable at all

⚠ **It records what INGEST did, never what anyone asked.** `test_no_row_carries
_a_query_field` is the L8 fence in test form, and `tests/test_import_fence.py`'s
companion here asserts no query-plane module imports it.
"""

from __future__ import annotations

import json
import os
import stat

import pytest

from fux.ingest import ingestlog as provenance
from fux.ingest.run import run


def _write_fetcher(root, text, name="mw.py", encoding="utf-8"):
    """Write a fixture fetcher where the resolver looks for it.

    ⚠ **`.fux/fetchers/` is the only place now.** Until 2026-09-20 a fixture
    could put a fetcher anywhere and point `[sources.url] fetcher` at it; that
    key is deleted (W-199 D2) and the directory is fixed, so the fixture creates
    it rather than relying on `fux setup` having run.
    """
    path = root / ".fux" / "fetchers" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


FETCHER = '''\
def fetch(url):
    return "# Page " + url.rsplit("/", 1)[-1] + chr(10) * 2 + "fetched body" + chr(10)
'''


def _repo(tmp_path, *, urls=(), files=None):
    """A minimal ingestable repo. Mirrors `tests/ingest/test_urlsrc.py::_init`."""
    files = files if files is not None else {"docs/a.md": "# Doc A\n\nrepo body\n"}
    toml = "[sources]\n"
    if urls:
        toml += '[sources.url]\nmax_parallel = 4\n'
        _write_fetcher(tmp_path, FETCHER)
    (tmp_path / "fux.toml").write_text(toml, encoding="utf-8")
    fux = tmp_path / ".fux"
    (fux / "sources").mkdir(parents=True, exist_ok=True)
    (fux / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (fux / "sources" / "urls").write_text(
        "".join(f"{u}\n" for u in urls), encoding="utf-8"
    )
    # SR-PII decision 17: every verb refuses without this file.
    (fux / "pii.toml").write_text("", encoding="utf-8")
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def _rows(root) -> dict[str, dict]:
    text = provenance.path_for(root).read_text(encoding="utf-8")
    return {json.loads(line)["id"]: json.loads(line) for line in text.splitlines() if line.strip()}


# --- the shape -----------------------------------------------------------


def test_one_row_per_document_naming_its_decoder(tmp_path):
    root = _repo(
        tmp_path,
        files={"docs/a.md": "# A\n\nbody\n", "docs/t.csv": "name,qty\nbolt,4\n"},
    )
    run(root)
    rows = _rows(root)
    assert set(rows) == {"file:docs/a.md", "file:docs/t.csv"}
    # Markdown carries no binding — W-166 says so, and `prose` is minted here
    # once rather than left as null for every reader to interpret.
    assert rows["file:docs/a.md"]["decoder"] == provenance.PROSE
    # A built-in decoder's digest is the string `decoderdigest` already mints.
    assert rows["file:docs/t.csv"]["decoder"].startswith("csv@")


def test_rows_are_sorted_by_id_with_sorted_keys(tmp_path):
    """Two machines ingesting the same tree write the same bytes (L3).

    The file is gitignored, so this is not a correctness property of the index
    — it is what makes a diff between two runs readable, which is the only
    reason anyone opens a ledger.
    """
    root = _repo(
        tmp_path,
        files={f"docs/{n}.md": f"# {n}\n\nbody\n" for n in ("c", "a", "b")},
    )
    run(root)
    lines = provenance.path_for(root).read_text(encoding="utf-8").splitlines()
    ids = [json.loads(line)["id"] for line in lines]
    assert ids == sorted(ids)
    for line in lines:
        keys = list(json.loads(line))
        assert keys == sorted(keys)


def test_a_file_row_carries_no_fetcher_key(tmp_path):
    """`None` is dropped, not written. A file row must not carry a key that can
    only ever be null for it — an absent key and a null one read differently to
    every consumer, and only one of them is true here."""
    root = _repo(tmp_path)
    run(root)
    assert "fetcher" not in _rows(root)["file:docs/a.md"]


# --- decision 2: clock-free, and decision 1's L8 fence --------------------


def test_no_row_carries_a_clock(tmp_path):
    """L3. `run_seq` is a counter `url-state.json` already owns.

    A wall-clock field would make the ledger non-reproducible, and anything
    that reads it would inherit that — which is the whole argument the acquired
    manifest already made.
    """
    root = _repo(tmp_path)
    run(root)
    for row in _rows(root).values():
        assert "run_seq" in row
        for key in ("time", "timestamp", "ts", "at", "when", "mtime", "date"):
            assert key not in row, f"{key!r} is a clock in a file that must have none"


def test_no_row_carries_a_query_field(tmp_path):
    """L8's fence, in test form.

    This ledger records what **ingest** did, so
    [L8](../../records/0010_LAW-8-use-record.md) does not reach it. **It must
    never grow a query field** — the moment a line here names a question, the
    file becomes a use record on a path L8 governs, and this test is the thing
    that would have to be deleted first.
    """
    root = _repo(tmp_path)
    run(root)
    for row in _rows(root).values():
        for key in ("query", "q", "asked", "question", "answer", "results", "hits"):
            assert key not in row


# --- decision 5: a reused row carries the PRIOR decoder -------------------


def test_a_reused_row_carries_the_decoder_that_made_the_record(tmp_path):
    """🔴 **The test that makes `doctor`'s stale-decoder finding fireable.**

    A reused record was not re-extracted, so the decoder that produced it is
    whatever produced it *then*. Writing the tree's current digest onto the row
    would make every row agree with the tree by construction — including on
    exactly the records that were **not** re-extracted, which is the only
    population the finding is about.
    """
    root = _repo(tmp_path, files={"docs/t.csv": "name,qty\nbolt,4\n"})
    run(root)
    first = _rows(root)["file:docs/t.csv"]
    assert first["outcome"] == "indexed"

    report = run(root)
    assert report.reused_count == 1, "the delta path must actually have reused it"
    second = _rows(root)["file:docs/t.csv"]
    assert second["outcome"] == "reused"
    assert second["decoder"] == first["decoder"]


def test_a_reused_row_with_no_prior_ledger_reads_unknown(tmp_path):
    """Absent and unknown are different, and only one means *"this predates the
    ledger"*. `null` would be read as *"no decoder"*, which is `prose`."""
    root = _repo(tmp_path, files={"docs/t.csv": "name,qty\nbolt,4\n"})
    run(root)
    provenance.path_for(root).unlink()  # simulate a repo that ingested before W-200
    run(root)
    assert _rows(root)["file:docs/t.csv"]["decoder"] == provenance.UNKNOWN


# --- decision 3: best-effort ----------------------------------------------


def test_an_unwritable_ledger_is_a_note_not_a_failure(tmp_path):
    """A ledger that can fail a run is worse than no ledger.

    The `_record_refusals` / `_record_stale_redaction` precedent: an advisory
    derived file must never be able to stop an ingest that otherwise succeeded.
    """
    root = _repo(tmp_path)
    run(root)
    target = provenance.path_for(root)
    target.write_text("{}\n", encoding="utf-8")
    runtime = target.parent
    mode = runtime.stat().st_mode
    os.chmod(runtime, mode & ~stat.S_IWUSR)
    try:
        report = run(root, full=True)  # must not raise
    finally:
        os.chmod(runtime, mode)
    assert report.doc_count == 1


def test_a_corrupt_ledger_reads_as_no_prior_run(tmp_path):
    """One bad line loses one row, never the file, and an unparseable file
    loses the run's history rather than the run."""
    root = _repo(tmp_path)
    run(root)
    provenance.path_for(root).write_text("not json\n{\n", encoding="utf-8")
    assert provenance.read(root) == {}
    run(root)  # must not raise


# --- decision 1: runtime, never committed ---------------------------------


def test_the_ledger_is_under_the_derived_directory(tmp_path):
    """A consumer decoder's sha differs between two machines, so a committed
    field would state a fact true on one of them — the argument that kept the
    blob sha off the record (SR-ACQUIRED). `.gitignore` already covers
    `.fux/runtime/`, which is why no new ignore line was needed."""
    root = _repo(tmp_path)
    run(root)
    rel = provenance.path_for(root).relative_to(root).as_posix()
    assert rel == ".fux/runtime/ingest-log.jsonl"


def test_the_ledger_is_not_the_answer_journal(tmp_path):
    """🔴 **The defect W-200's spec had, pinned so it cannot come back.**

    The spec named `.fux/runtime/ingest-log.jsonl`, which is already
    `fux.query.provenance`'s **answer journal** — an L8 use record written only
    under explicit consent (W-147: the flag *and* the output-TOML key). Writing
    this ledger there would have made **every `fux ingest` create a file that
    is supposed to require consent**.

    Caught by `tests_e2e/test_verbs.py::test_both_journal_consent_surfaces_
    write_and_neither_alone_is_removable` — *"a journal appeared with no consent
    of any kind"*. Asserted here too, because the e2e test is about consent and
    would not explain why the path moved.
    """
    from fux.query.provenance import JOURNAL_NAME

    root = _repo(tmp_path)
    run(root)
    assert provenance.path_for(root).name != JOURNAL_NAME
    assert not (root / ".fux" / "runtime" / JOURNAL_NAME).exists()


# --- URL rows --------------------------------------------------------------


def test_a_url_row_carries_its_fetcher_and_decoder(tmp_path):
    root = _repo(tmp_path, urls=["https://x.test/a fetch=mw decoder=prose"])
    run(root, refresh_urls=True)
    row = _rows(root)["url:https://x.test/a"]
    assert row["kind"] == "url"
    assert row["loc"] == "https://x.test/a"
    assert row["outcome"] == "indexed"
    # A fetcher has no VERSION: the consumer owns the file, so its sha IS its
    # version — the rule a consumer decoder already follows.
    assert row["fetcher"].startswith("mw@sha:")
    assert row["raw_bytes"] > 0


def test_a_skipped_url_gets_a_row_saying_why(tmp_path):
    """*"Nothing was indexed from this path and here is why"* is the question
    the ledger is most often opened for, and `docs.jsonl` can never answer it —
    a skipped document has no record to appear in.

    ⚠ **A URL, not a file, and the choice is not arbitrary.** A file fux cannot
    read is usually a file fux was never asked to read: `.pdf` is outside the
    default `include` globs, so it is *not a document* rather than *a skipped
    one*, and no row is right for it. A URL is listed explicitly, so a fetch
    that fails is always a skip.
    """
    root = _repo(tmp_path, urls=["https://x.test/gone fetch=mw decoder=prose"])
    _write_fetcher(root, 
        "def fetch(url):\n    raise RuntimeError('404 not found')\n", encoding="utf-8"
    )
    run(root, refresh_urls=True)
    rows = _rows(root)
    row = rows["url:https://x.test/gone"]
    assert row["outcome"].startswith("skipped:")
    assert "404" in row["outcome"], "the reason must be carried, not flattened"
    assert row["kind"] == "url"


# --- the helper's own contract --------------------------------------------


@pytest.mark.parametrize(
    "row_decoder,current,expected",
    [
        ("csv@sha:aaaa", {".csv": "csv@sha:bbbb"}, 1),   # moved
        ("csv@sha:aaaa", {".csv": "csv@sha:aaaa"}, 0),   # current
        (provenance.PROSE, {".csv": "csv@sha:bbbb"}, 0),  # no binding claims it
        (provenance.UNKNOWN, {".csv": "csv@sha:bbbb"}, 0),  # predates the ledger
        ("gone@sha:aaaa", {".csv": "csv@sha:bbbb"}, 0),  # decoder no longer bound
    ],
)
def test_stale_decoder_count_only_counts_what_a_full_ingest_would_fix(
    tmp_path, row_decoder, current, expected
):
    """⚠ **`prose` and `unknown` are never stale**, and that is the care here:
    no binding claims Markdown, and `unknown` means the ledger predates the row
    rather than that the decoder moved. Counting either would report a number
    no command can bring down, which is how a doctor row gets ignored."""
    root = _repo(tmp_path)
    provenance.write(
        root,
        [
            provenance.Row(
                id="file:docs/t.csv",
                kind="file",
                loc="docs/t.csv",
                outcome="reused",
                run_seq=0,
                decoder=row_decoder,
            )
        ],
    )
    assert provenance.stale_decoder_count(root, current) == expected
