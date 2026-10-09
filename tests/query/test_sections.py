"""W-236 — section records (SR-SECTIONS), Part B's build.

What is pinned here, in the record's order:

1. **The index section rule** (decision 2): heading depth, a bodiless section
   folding forward into a deeper one, one section or none → sectionless.
2. **The plane** (decisions 1, 3, 4): `doc#s<k>` lines in the parent's shard
   under `.fux/index/sections/`, `nsec` on the document, totality.
3. **Off is off** (decision 7): at `section_weight = 0.0` the ranking and the
   `--json` hit are what they were without section records.
4. **The differential law at λ > 0**: the scan and the accelerator — skipping
   on — return identical lists, and the widened ceiling still bounds. **The
   term is gain-only** (W-269): a sectionless document scores at every λ
   exactly what it scores at 0.0, and a document whose words are spread over
   its sections gains nothing.
5. **The two planes are held together** (decision 9): `fux build` refuses a
   disagreement rather than diverging.
6. **Carried with the document** (decision 8): an unchanged document keeps its
   section lines byte for byte; a deleted one takes them with it.
"""

from __future__ import annotations

import dataclasses
import json

import pytest
from l12_fixtures import scoring, write_config

from fux import store
from fux.derive import accel, build
from fux.errors import FuxError
from fux.ingest.run import run
from fux.query import scan
from fux.refer._chunk import index_sections

OFF = dataclasses.replace(scoring(), section=0.0)
TOPS = (1, 3, 10)


def on(weight: float = 1.0):
    return dataclasses.replace(scoring(), section=weight)


def _init(tmp_path, files: dict[str, str]) -> None:
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    write_config(tmp_path)
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _long_doc() -> str:
    """A long runbook whose answer is ONE short heading section."""
    parts = ["# Operations runbook\n", "## Overview\n"]
    parts += [f"general operational prose line {i} about servers and queues\n" for i in range(60)]
    parts += ["## Rollback procedure\n", "to rollback the canary deploy run the rollback script\n"]
    parts += ["## Appendix\n"] + [f"appendix filler line {i} on unrelated tooling\n" for i in range(60)]
    return "".join(parts)


@pytest.fixture
def corpus(tmp_path):
    files = {
        "docs/runbook.md": _long_doc(),
        "docs/short.md": "# Canary\n\nthe canary deploy is a staged rollout\n",
        "docs/rollback-note.md": "# Rollback\n\nrollback means returning to the previous release\n",
        "docs/one-section.md": "# Lonely\n\nonly one section, rollback mentioned once\n",
        # W-269: the query words spread evenly over two sections, so the
        # document as one unit outscores either section and gains nothing.
        "docs/spread.md": "# Spread\n\n## East\n\nzebra quokka\n\n## West\n\nzebra quokka\n",
    }
    for i in range(25):
        files[f"docs/filler-{i:02d}.md"] = (
            f"# Filler {i}\n\n## Part a\n\nfiller text {i} about queues\n\n## Part b\n\nmore filler {i}\n"
        )
    _init(tmp_path, files)
    run(tmp_path, refresh_urls=False, full=False)
    build(tmp_path)
    return tmp_path


# -- 1. the section rule ------------------------------------------------------


def test_a_bodiless_title_folds_into_the_deeper_section_it_introduces():
    texts = index_sections("# Title\n\n## A\n\nalpha body\n\n## B\n\nbeta body\n")
    assert len(texts) == 2
    assert texts[0].startswith("# Title") and "alpha body" in texts[0]
    assert "beta body" in texts[1]


def test_siblings_never_fold_whatever_their_size():
    texts = index_sections("## One\n\nx\n\n## Two\n\ny\n\n## Three\n\nz\n")
    assert len(texts) == 3


def test_a_preamble_is_a_section():
    texts = index_sections("intro words\n\n## A\n\nbody\n")
    assert texts == ["intro words", "## A\n\nbody"]


def test_a_single_heading_document_is_one_section():
    assert len(index_sections("# Only\n\nsome text\n")) == 1


# -- 2. the plane -------------------------------------------------------------


def test_a_multi_section_document_gets_nsec_and_section_lines(corpus):
    records = store.read_index(corpus)
    sections = store.read_sections(corpus)
    runbook = records["file:docs/runbook.md"]
    assert runbook["nsec"] == len(sections["file:docs/runbook.md"]) == 3
    assert [s["id"] for s in sections["file:docs/runbook.md"]] == [
        "file:docs/runbook.md#s1", "file:docs/runbook.md#s2", "file:docs/runbook.md#s3",
    ]
    for section in sections["file:docs/runbook.md"]:
        assert set(section) == {"id", "flen", "terms"}
        assert len(section["flen"]) <= store.SECTION_SLOTS


def test_a_sectionless_document_has_no_nsec_and_no_lines(corpus):
    records = store.read_index(corpus)
    sections = store.read_sections(corpus)
    for doc_id in ("file:docs/short.md", "file:docs/one-section.md"):
        assert "nsec" not in records[doc_id]
        assert doc_id not in sections


def test_totality_sections_sum_to_the_document(corpus):
    """SR-SECTIONS decision 3's invariant, on every multi-section document."""
    records = store.read_index(corpus)
    for parent, secs in store.read_sections(corpus).items():
        doc = records[parent]
        for slot in range(store.SECTION_SLOTS):
            total = sum((s["flen"] + [0] * store.SECTION_SLOTS)[slot] for s in secs)
            assert total == (doc["flen"] + [0] * store.SECTION_SLOTS)[slot], (parent, slot)
        for term, tf in doc["terms"].items():
            want = (tf + [0] * store.SECTION_SLOTS)[: store.SECTION_SLOTS]
            got = [0] * store.SECTION_SLOTS
            for s in secs:
                for i, count in enumerate(s["terms"].get(term, [])):
                    got[i] += count
            assert got == want, (parent, term)


def test_section_lines_live_in_their_parents_shard(corpus):
    for path in store.iter_section_paths(corpus):
        for line in path.read_bytes().split(b"\n")[1:]:
            if line:
                parent = store.section_parent(json.loads(line)["id"])
                assert store.shard_for(parent) == path.stem


def test_no_document_reader_sees_the_section_plane(corpus):
    """Decision 1's reason: `iter_shard_paths` never yields a section shard."""
    assert all(p.parent == store.index_dir(corpus) for p in store.iter_shard_paths(corpus))
    assert not any("#s" in doc_id for doc_id in store.read_index(corpus))


# -- 3. off is off -------------------------------------------------------------


@pytest.mark.parametrize("top", TOPS)
def test_at_zero_the_scan_never_opens_the_plane(corpus, top, monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("the section plane was read at section_weight = 0")

    monkeypatch.setattr(store, "iter_section_paths", boom)
    monkeypatch.setattr(accel.Runtime, "section_postings", boom)
    results = scan.ask(corpus, "rollback canary deploy", top, scoring=OFF)
    assert results
    assert accel.ask(corpus, "rollback canary deploy", top, skipping=True, scoring=OFF) == results
    assert all(r.section is None for r in results)


def test_at_zero_scores_equal_an_index_without_section_records(corpus, tmp_path_factory):
    """Byte identity at 0.0 (decision 7): delete the plane and drop `nsec`,
    and nothing about the ranking moves."""
    stripped = tmp_path_factory.mktemp("stripped")
    import shutil

    shutil.copytree(corpus, stripped, dirs_exist_ok=True)
    records = list(store.read_index(stripped).values())
    store.write_index(stripped, records)  # no `sections` key: the plane goes
    assert not store.iter_section_paths(stripped)
    for query in ("rollback canary deploy", "queues filler", "appendix tooling"):
        assert scan.ask(stripped, query, 10, scoring=OFF) == scan.ask(corpus, query, 10, scoring=OFF)


# -- 4. on: the term moves, and both paths agree --------------------------------


def test_the_best_section_lifts_the_long_document(corpus):
    query = "rollback canary deploy script"
    off = [r.id for r in scan.ask(corpus, query, 5, scoring=OFF)]
    lifted = scan.ask(corpus, query, 5, scoring=on(1.0))
    assert lifted[0].id == "file:docs/runbook.md", (off, [r.id for r in lifted])
    assert lifted[0].section == "file:docs/runbook.md#s2"


def test_a_sectionless_hit_names_no_section(corpus):
    results = scan.ask(corpus, "staged rollout", 5, scoring=on(1.0))
    short = next(r for r in results if r.id == "file:docs/short.md")
    assert short.section is None


SECTIONLESS = ("file:docs/short.md", "file:docs/rollback-note.md", "file:docs/one-section.md")


@pytest.mark.parametrize("weight", [0.25, 0.5, 1.0, 2.0, 4.0])
@pytest.mark.parametrize("query", ["rollback canary deploy script", "staged rollout rollback", "rollback"])
def test_a_sectionless_document_scores_exactly_what_it_scores_at_zero(corpus, weight, query):
    """W-269's G3 on the fixture: the gain-only term gives a sectionless
    document NOTHING, so its score is byte-identical to `0.0` on both paths.
    B2 as W-236 built it gave each of these `λ ×` its whole body score."""
    off = {r.id: r.score for r in scan.ask(corpus, query, 50, scoring=OFF)}
    for results in (
        scan.ask(corpus, query, 50, scoring=on(weight)),
        accel.ask(corpus, query, 50, skipping=False, scoring=on(weight)),
    ):
        got = {r.id: r for r in results}
        compared = [d for d in SECTIONLESS if d in off]
        assert compared, query
        for doc in compared:
            assert got[doc].score == off[doc], (doc, weight)
            assert got[doc].section is None


def test_a_document_whose_words_are_spread_gains_nothing(corpus):
    """Each section holds half of the tf; the document as one unit holds all
    of it, so `max_k S_sec <= S_self` and `G = 0`."""
    stats: dict = {}
    off = {r.id: r.score for r in scan.ask(corpus, "zebra quokka", 5, scoring=OFF)}
    results = scan.ask(corpus, "zebra quokka", 5, scoring=on(2.0), stats_out=stats)
    spread = next(r for r in results if r.id == "file:docs/spread.md")
    assert store.read_index(corpus)["file:docs/spread.md"]["nsec"] == 2
    assert spread.score == off["file:docs/spread.md"]
    assert spread.section is None
    assert stats["sections"]["file:docs/spread.md"] == (None, 0.0)


def test_the_gain_is_the_best_section_minus_the_document_as_one_unit(corpus):
    """The `--why` contribution is `λ · G`, and G is strictly below the best
    section's own score: the document's whole-unit score is subtracted."""
    query = "rollback canary deploy script"
    one = {}
    two = {}
    scan.ask(corpus, query, 5, scoring=on(1.0), stats_out=one)
    scan.ask(corpus, query, 5, scoring=on(2.0), stats_out=two)
    sec_id, gain = one["sections"]["file:docs/runbook.md"]
    assert sec_id == "file:docs/runbook.md#s2" and gain > 0
    assert two["sections"]["file:docs/runbook.md"] == (sec_id, 2.0 * gain)


@pytest.mark.parametrize("weight", [0.1, 0.25, 0.5, 1.0, 4.0])
@pytest.mark.parametrize("top", TOPS)
@pytest.mark.parametrize("query", ["rollback canary deploy script", "filler queues", "appendix tooling servers"])
def test_the_accelerator_equals_the_scan_at_every_weight(corpus, weight, top, query):
    want = scan.ask(corpus, query, top, scoring=on(weight))
    assert accel.ask(corpus, query, top, skipping=True, scoring=on(weight)) == want
    assert accel.ask(corpus, query, top, skipping=False, scoring=on(weight)) == want


def test_the_why_seam_carries_the_section_contribution(corpus):
    stats: dict = {}
    results = scan.ask(corpus, "rollback canary deploy script", 3, scoring=on(1.0), stats_out=stats)
    sec_id, contribution = stats["sections"][results[0].id]
    assert sec_id == results[0].section and contribution > 0


# -- 5. the planes held together ------------------------------------------------


def test_build_refuses_a_document_whose_nsec_disagrees(corpus):
    path = store.shard_path(corpus, store.shard_for("file:docs/runbook.md"))
    path.write_bytes(path.read_bytes().replace(b'"nsec":3', b'"nsec":4'))
    with pytest.raises(FuxError, match="nsec=4"):
        build(corpus)


def test_build_refuses_an_orphan_section(corpus):
    parent = "file:docs/runbook.md"
    path = store.section_shard_path(corpus, store.shard_for(parent))
    orphan = store.canonical_dumps({"id": "file:docs/ghost.md#s1", "flen": [1], "terms": {}})
    # The orphan's own shard: placement is checked by the reader too.
    ghost = store.section_shard_path(corpus, store.shard_for("file:docs/ghost.md"))
    ghost.parent.mkdir(parents=True, exist_ok=True)
    head = path.read_bytes().split(b"\n", 1)[0] + b"\n"
    ghost.write_bytes((ghost.read_bytes() if ghost.exists() else head) + orphan)
    with pytest.raises(FuxError, match="not in the index"):
        build(corpus)


# -- 6. carried with the document --------------------------------------------------


def test_an_unchanged_document_keeps_its_section_lines(corpus):
    before = {p.name: p.read_bytes() for p in store.iter_section_paths(corpus)}
    (corpus / "docs" / "short.md").write_text("# Canary\n\nchanged text\n", encoding="utf-8")
    report = run(corpus, refresh_urls=False, full=False)
    assert report.reused_count > 0
    assert {p.name: p.read_bytes() for p in store.iter_section_paths(corpus)} == before


def test_a_deleted_document_takes_its_sections_with_it(corpus):
    (corpus / "docs" / "runbook.md").unlink()
    run(corpus, refresh_urls=False, full=False)
    assert "file:docs/runbook.md" not in store.read_sections(corpus)
    build(corpus)  # and the planes still agree


# -- 7. the merge driver: a parent's sections are one unit (decision 9) --------

from fux.maintain.mergedriver import MergeConflict, merge_sections  # noqa: E402

_HEAD = '{"_format":"x"}'


def _sec(parent: str, k: int, n: int) -> str:
    return json.dumps({"flen": [n], "id": f"{parent}#s{k}", "terms": {}}, separators=(",", ":"), sort_keys=True)


def _shard(*lines: str) -> str:
    return "\n".join([_HEAD, *lines]) + "\n"


def test_a_one_sided_section_change_merges():
    base = _shard(_sec("file:a.md", 1, 1), _sec("file:a.md", 2, 1))
    ours = _shard(_sec("file:a.md", 1, 5), _sec("file:a.md", 2, 5), _sec("file:a.md", 3, 5))
    assert merge_sections(base, ours, base) == ours


def test_sections_never_mix_across_sides():
    """Ours changed `#s1`, theirs changed `#s2` of the SAME document: a
    line-wise merge would build a set matching neither side. Refused."""
    base = _shard(_sec("file:a.md", 1, 1), _sec("file:a.md", 2, 1))
    ours = _shard(_sec("file:a.md", 1, 9), _sec("file:a.md", 2, 1))
    theirs = _shard(_sec("file:a.md", 1, 1), _sec("file:a.md", 2, 9))
    with pytest.raises(MergeConflict) as exc:
        merge_sections(base, ours, theirs)
    assert exc.value.ids == ["file:a.md"]


def test_different_documents_merge_independently():
    base = _shard(_sec("file:a.md", 1, 1), _sec("file:a.md", 2, 1))
    ours = _shard(_sec("file:a.md", 1, 1), _sec("file:a.md", 2, 1), _sec("file:b.md", 1, 2), _sec("file:b.md", 2, 2))
    theirs = _shard(_sec("file:a.md", 1, 7), _sec("file:a.md", 2, 7))
    merged = merge_sections(base, ours, theirs)
    assert _sec("file:a.md", 1, 7) in merged and _sec("file:b.md", 2, 2) in merged
