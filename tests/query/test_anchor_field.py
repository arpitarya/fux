"""W-168 step 1 — the anchor field, from retrieval through to the two readers.

**The two traps the work item wrote down as done-ness rather than leaving to
be discovered**, and each has a test here:

1. **Step 1 is a RETRIEVAL change, not a scoring one.** A document is never a
   candidate for a word it does not contain, so a scoring fold alone does
   nothing at all for the documents this feature exists for.
2. **The fold must land once, in the shared read path.** `query/rank.py` states
   the contract — *"the accelerator's build asserts it reproduces the same
   statistics"* — so a one-sided fold ships `--fast`/`--scan` drift, silently
   and data-dependently.
"""

from __future__ import annotations

import json

import pytest

from fux import store
from fux.derive import accel, build
from fux.ingest.run import run
from fux.query import scan
from fux.query.bm25f import DEFAULT_SCORING, Scoring

#: Non-zero, because `0.0` is the shipped default and would exercise nothing.
ON = Scoring(anchor=2.0)

TOPS = (1, 5, 20)


def _init(tmp_path, files: dict[str, str]) -> None:
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


@pytest.fixture
def corpus(tmp_path):
    """`zarquon` appears in NO document's body — only in the words two other
    documents use to link to `target.md`.

    That is SR-RS decision 23 in miniature: the data has to contain the input
    the feature acts on, or a measurement of it measures nothing.
    """
    files = {
        "docs/target.md": "# Widget\n\nthis page explains the widget machinery in detail\n",
        "docs/linker-one.md": "# One\n\nSee [the zarquon protocol](target.md) for details.\n",
        "docs/linker-two.md": "# Two\n\nThe [zarquon](target.md) is documented elsewhere.\n",
        "docs/decoy.md": "# Decoy\n\nan unrelated page about machinery and details\n",
    }
    for i in range(30):
        files[f"docs/filler-{i:02d}.md"] = f"# Filler {i}\n\nfiller body text number {i}\n"
    _init(tmp_path, files)
    run(tmp_path)
    build(tmp_path)
    return tmp_path


def _ids(results):
    return [r.id for r in results]


# -- trap 1: retrieval ------------------------------------------------------


def test_off_by_default_the_TARGET_is_unreachable(corpus):
    """The baseline this feature is measured against, and the shipped default.

    ⚠ **The linkers still match, and that is not a broken fixture.** Link text
    is part of the sentence it sits in, so a document that writes
    `[the zarquon protocol](target.md)` has *zarquon* in its own body and its
    own postings. What no query can reach without the anchor field is the page
    the word is ABOUT — which is the whole gap, and why the assertion below is
    about `target.md` and not about the result list being empty.
    """
    for ask in (scan.ask, accel.ask):
        ids = _ids(ask(corpus, "zarquon", top=5))
        assert "file:docs/target.md" not in ids, ids
        assert "file:docs/linker-one.md" in ids


def test_a_document_is_reachable_by_what_its_LINKERS_call_it(corpus):
    """🔴 Trap 1. Without the second pass in `scan_candidates` this is empty:
    `target.md`'s own line carries none of the query's hashes, so the byte
    prefilter never looked at it and no scoring fold could rescue it."""
    hits = scan.ask(corpus, "zarquon", top=5, scoring=ON)
    assert _ids(hits)[0] == "file:docs/target.md", _ids(hits)
    assert accel.ask(corpus, "zarquon", top=5, scoring=ON)[0].id == "file:docs/target.md"


def test_the_linkers_themselves_are_also_hits(corpus):
    """They contain the word in their own bodies — anchor text is taken from
    the link, and the link is part of the sentence around it. Nothing about
    this feature should suppress the document that used the word."""
    ids = _ids(scan.ask(corpus, "zarquon", top=5, scoring=ON))
    assert "file:docs/linker-one.md" in ids
    assert "file:docs/linker-two.md" in ids


def test_anchor_terms_do_not_move_df(corpus):
    """Switching the field on must not change `idf` for anything.

    Anchor terms are in no committed posting, so they are in no `df` — and
    `derive/accel.py` counts `df` from the postings alone, so counting them on
    the scan side would be an immediate differential-law break.
    """
    off, on = {}, {}
    scan.ask(corpus, "widget machinery", top=5, stats_out=off)
    scan.ask(corpus, "widget machinery", top=5, scoring=ON, stats_out=on)
    assert off["df"] == on["df"]
    assert off["n"] == on["n"]


# -- trap 2: one fold, both paths ------------------------------------------


def _payload(results) -> str:
    """Exactly what `fux ask --json` prints — the surface under test."""
    return json.dumps({"results": [r.__dict__ for r in results]}, indent=2)


@pytest.mark.parametrize("query", ["zarquon", "zarquon protocol", "widget", "machinery details"])
@pytest.mark.parametrize("top", TOPS)
@pytest.mark.parametrize("skipping", [False, True])
def test_the_scan_and_the_accelerator_agree_with_the_field_on(corpus, query, top, skipping):
    """🔴 Trap 2, made checkable. The fold lives in `rank()`, which both paths
    reach; the accelerator's job is to hand `rank()` the same candidate records
    the scan does, `atf` and `alen` included."""
    expected = _payload(scan.ask(corpus, query, top=top, scoring=ON))
    got = _payload(accel.ask(corpus, query, top=top, scoring=ON, skipping=skipping))
    assert got == expected, f"query={query!r} top={top} skipping={skipping}"


def test_both_generators_attach_the_anchor_keys_to_EVERY_candidate(corpus):
    """`atf` may be empty; `alen` may not be.

    A document that is linked-to is a longer document whether or not the
    query's words are what its linkers used. Attaching the keys only where
    `atf` is non-empty would drop those documents' anchor length out of `wlen`
    on one path and not the other — which is the divergence the shared fold
    exists to make impossible, and it would show up only on linked documents.
    """
    hashes = scan.query_term_hashes("machinery")
    scanned, _, _ = scan.scan_candidates(corpus, hashes, scoring=ON)
    assert scanned
    for record in scanned:
        assert "atf" in record and "alen" in record, record["id"]

    runtime = accel.Runtime(corpus)
    accelerated, _, _ = accel.accel_candidates(runtime, hashes, 5, scoring=ON)
    assert accelerated
    for record in accelerated:
        assert "atf" in record and "alen" in record, record["id"]


def test_the_two_paths_agree_on_avg_wlen(corpus):
    """`total_anchor_len` is summed off raw bytes on one path and read from
    `stats.json` on the other. They are the same number or every score differs
    in its denominator."""
    hashes = scan.query_term_hashes("widget")
    _, _, scan_corpus = scan.scan_candidates(corpus, hashes, scoring=ON)
    _, _, accel_corpus = accel.accel_candidates(accel.Runtime(corpus), hashes, 5, scoring=ON)
    assert scan_corpus.n == accel_corpus.n
    assert scan_corpus.total_wlen == accel_corpus.total_wlen


# -- the default path is untouched -----------------------------------------


@pytest.mark.parametrize("query", ["widget", "machinery details", "filler body text"])
def test_the_default_scores_byte_identically_to_no_anchor_field(corpus, query):
    """`0.0` is not "weight zero" — every anchor branch is skipped entirely, so
    an unconfigured corpus does the float arithmetic it did before the field
    existed. That is the `term_weights` precedent, and it is what keeps the
    differential evidence gathered at the default standing unmodified."""
    assert DEFAULT_SCORING.anchor == 0.0
    assert not DEFAULT_SCORING.anchor_on
    assert DEFAULT_SCORING.trivial
    expected = _payload(scan.ask(corpus, query, top=20))
    assert _payload(scan.ask(corpus, query, top=20, scoring=DEFAULT_SCORING)) == expected
    assert _payload(accel.ask(corpus, query, top=20)) == expected


def test_a_stale_runtime_is_refused_rather_than_read(corpus):
    """The doc table grew `alen` and `stats.json` grew `total_anchor_len`, so a
    pre-v6 plane cannot answer an anchor query — and must not try.

    This is the 2026-08-23 lesson `DOCS_FIELDS` exists for: a field added to
    the table while the schema string stayed put left an accelerator built
    minutes earlier still being read, and `--scan` and `--fast` weighted the
    same document differently.
    """
    from fux.derive import format as fmt

    manifest_path = fmt.runtime_dir(corpus) / fmt.MANIFEST_NAME
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest["schema"] == "fux.runtime.v6"
    assert manifest["docs_fields"][-1] == "alen"
    manifest["schema"] = "fux.runtime.v5"
    manifest_path.write_bytes(json.dumps(manifest).encode("utf-8"))
    assert not accel.is_fresh(corpus)


def test_anchor_length_reaches_wlen(corpus):
    """A linked-to document is a LONGER document.

    Leaving anchor out of the normaliser is what lets a link farm max out a
    term with no length price, so it is in — and this is the assertion that
    says so, because nothing else would notice it being dropped.
    """
    index = store.read_index(corpus)
    target = index["file:docs/target.md"]
    docs = json.loads(
        (accel.fmt.runtime_dir(corpus) / accel.fmt.DOCS_NAME).read_bytes().split(b"\n")[0]
    )
    assert isinstance(docs["alen"], int)
    by_id = {}
    raw = (accel.fmt.runtime_dir(corpus) / accel.fmt.DOCS_NAME).read_bytes()
    for line in raw.split(b"\n"):
        if line:
            row = json.loads(line)
            by_id[row["id"]] = row
    # Two documents link to it, with three indexable words between them.
    assert by_id["file:docs/target.md"]["alen"] > 0
    # ...and a document nobody links to carries nothing.
    assert by_id["file:docs/decoy.md"]["alen"] == 0
    assert target["terms"], "fixture sanity"
