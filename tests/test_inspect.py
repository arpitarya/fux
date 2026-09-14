"""`fux inspect`'s parts, on corpora small enough to reason about by hand.

The lens-by-lens proof on a **planted** corpus — each lens must name its own
plant and nothing else — is `tests_e2e/test_inspect.py`, because a plant only
means something once ingest has actually written it. What is here is the
arithmetic: the sampling, the minhash, the percentile rule, the truncation
counts, and the two shapes that must never raise.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fux.inspect import _scan, checks as checks_mod, dictionary as dictionary_mod, lenses


# --------------------------------------------------------------------------
# the sampling rule


def test_the_retrieval_sample_is_evenly_spaced_and_not_the_first_k() -> None:
    """Sorted-by-id order is directory order: the first `k` is one folder.

    On this repository the first 100 documents by id are all of `archive/`
    and none of `src/`, so a leading slice would report the archive's
    findability as the corpus's.
    """
    indices = lenses._sample_indices(1000, 10)
    assert indices == [0, 100, 200, 300, 400, 500, 600, 700, 800, 900]


def test_a_sample_at_or_above_the_corpus_is_every_document() -> None:
    assert lenses._sample_indices(5, 5) == [0, 1, 2, 3, 4]
    assert lenses._sample_indices(5, 99) == [0, 1, 2, 3, 4]


def test_zero_means_every_document_not_none_of_them() -> None:
    """`--retrieval-sample 0` asks for all of them. It is the one value where
    "falsy" and "the default" would silently disagree with the help text."""
    assert lenses._sample_indices(4, 0) == [0, 1, 2, 3]


def test_an_empty_corpus_samples_nothing_rather_than_dividing_by_zero() -> None:
    assert lenses._sample_indices(0, 10) == []


# --------------------------------------------------------------------------
# percentiles


def test_every_percentile_is_a_value_some_document_actually_has() -> None:
    """Nearest rank, never interpolated — an interpolated median is a token
    count no document carries, and a reader who goes looking will not find it."""
    values = [1, 2, 4, 8, 16]
    out = lenses._percentiles(values)
    assert out["min"] == 1 and out["max"] == 16
    for key, value in out.items():
        assert value in values, key


def test_percentiles_of_nothing_are_absent_not_zero() -> None:
    assert lenses._percentiles([]) == {}


# --------------------------------------------------------------------------
# minhash and Jaccard


def _fake_view(term_sets: list[list[int]]):
    """An `IndexView` carrying only what the duplication lens reads."""
    from array import array

    view = _scan.IndexView()
    for i, terms in enumerate(term_sets):
        view.docs.append(
            _scan.Doc(
                id=f"file:d{i}.md",
                loc=f"d{i}.md",
                title=f"d{i}",
                sha="",
                src="git",
                mode="extracted",
                archived=False,
                superseded=False,
                flen=(10, 1, 1, 1),
                nterms=len(terms),
                phrases=(),
                edges_out=0,
            )
        )
        view.doc_terms.append(array("i", sorted(terms)))
    highest = max((max(t) for t in term_sets if t), default=-1)
    view.term_of = [f"{i:016x}" for i in range(highest + 1)]
    view.term_value = array("Q", [int(h, 16) for h in view.term_of])
    view.df = array("i", [1] * (highest + 1))
    view.cf = array("q", [1] * (highest + 1))
    return view


def test_two_identical_documents_are_a_pair_at_jaccard_one() -> None:
    view = _fake_view([list(range(50)), list(range(50)), list(range(100, 150))])
    out = lenses.duplication(view)
    assert out.pair_count == 1
    left, right, score = out.near_duplicates[0]
    assert {left, right} == {"file:d0.md", "file:d1.md"}
    assert score == pytest.approx(1.0)
    assert out.documents_in_a_pair == 2


def test_two_disjoint_documents_are_not_a_pair() -> None:
    view = _fake_view([list(range(50)), list(range(100, 150))])
    assert lenses.duplication(view).pair_count == 0


def test_the_reported_number_is_the_exact_jaccard_not_the_estimate() -> None:
    """The estimate finds candidates; the set intersection is what prints.

    A 64-permutation estimate is a multiple of 1/64, so a reported 0.86 that
    happened to equal an estimate would be indistinguishable from the exact
    value. This pair's exact Jaccard is 90/110, which is not.
    """
    view = _fake_view([list(range(100)), list(range(10, 110))])
    out = lenses.duplication(view)
    assert out.pair_count == 1
    assert out.near_duplicates[0][2] == pytest.approx(90 / 110)


def test_a_document_with_no_terms_has_no_signature_and_no_pair() -> None:
    """Two empty documents are not near-duplicates of each other: Jaccard over
    two empty sets is undefined, and reporting 1.0 would pair every stub in a
    corpus with every other."""
    view = _fake_view([[], [], list(range(20))])
    assert lenses.duplication(view).pair_count == 0


# --------------------------------------------------------------------------
# truncation — decision 13


def test_a_truncated_list_reports_the_full_count_beside_it() -> None:
    """Found on this repo's own first report: orphans read `20` and were 341."""
    view = _fake_view([list(range(50)) for _ in range(12)])
    out = lenses.duplication(view, top_lists=3)
    assert len(out.near_duplicates) == 3
    assert out.pair_count == 66  # every pair of twelve identical documents
    assert out.documents_in_a_pair == 12


# --------------------------------------------------------------------------
# the checks


def test_a_check_with_no_value_is_n_a_and_never_a_pass() -> None:
    """Treating an absent number as a pass is how a broken instrument reads as
    a healthy corpus."""
    check = checks_mod.Check(
        name="x", value=None, floor=checks_mod.FLOORS["unreachable share"], detail=""
    )
    assert check.status == "n/a"
    assert check.flagged is False


def test_a_number_with_no_floor_is_descriptive_and_not_n_a() -> None:
    """The three states are distinct on purpose: `descriptive` means there IS a
    number and no floor could separate a healthy corpus from a bad one, which
    is a different statement from *we could not measure it*."""
    check = checks_mod.Check(name="findable share", value=1.0, floor=None, detail="")
    assert check.status == "descriptive"
    assert check.flagged is False


def test_findable_share_is_reported_and_carries_no_floor() -> None:
    """Decision 9a. Measured at 1.000 on every golden rung AND on the
    planted-bad corpus, so no bound separates them — the number prints and the
    flag does not."""
    assert "findable share" not in checks_mod.FLOORS


def test_every_floor_says_it_is_provisional() -> None:
    for name, floor in checks_mod.FLOORS.items():
        assert floor.provisional is True, name
        assert floor.source, name


def test_a_max_floor_flags_above_and_not_below() -> None:
    boiler = checks_mod.FLOORS["boilerplate share"]
    assert boiler.flags(0.9) and not boiler.flags(0.01)
    unreachable = checks_mod.FLOORS["unreachable share"]
    assert unreachable.flags(0.05) and not unreachable.flags(0.0)


def test_a_min_floor_flags_below_and_not_above() -> None:
    """No floor ships in this direction today; the mechanism still has to work,
    or the first `min` floor added would silently never fire."""
    floor = checks_mod.Floor(name="x", bound=0.9, direction="min", provisional=True, source="t")
    assert floor.flags(0.5) and not floor.flags(0.95)


def test_the_three_checks_are_three() -> None:
    """Decision 9: exactly three numbers carry a flag, and only three."""
    assert sorted(checks_mod.FLOORS) == [
        "boilerplate share",
        "near-duplicate share",
        "unreachable share",
    ]


# --------------------------------------------------------------------------
# what must never raise


def test_a_repository_with_no_index_says_so_rather_than_tracing_back(tmp_path) -> None:
    from fux.errors import FuxError
    from fux.inspect import inspect_index

    (tmp_path / ".fux").mkdir()
    with pytest.raises(FuxError) as excinfo:
        inspect_index(tmp_path)
    assert "fux ingest" in str(excinfo.value)


def test_a_dictionary_from_another_index_is_refused_rather_than_joined(tmp_path) -> None:
    """The cache key is the shard CONTENT SHAS, never an mtime.

    An mtime reports a `git checkout` as fresh, and the dictionary would then
    name a vocabulary the index no longer has — words for hashes that moved.
    """
    view = _scan.IndexView()
    view.shards = {"00.jsonl": "a" * 40}
    directory = dictionary_mod.inspect_dir(tmp_path)
    (directory / dictionary_mod.DICTIONARY_NAME).write_text(
        json.dumps({"schema": dictionary_mod.SCHEMA, "shards": {"00.jsonl": "b" * 40}, "terms": {}}),
        encoding="utf-8",
    )
    assert dictionary_mod.load(tmp_path, view) is None
    view.shards = {"00.jsonl": "b" * 40}
    assert dictionary_mod.load(tmp_path, view) is not None


def test_an_unnamed_hash_prints_as_itself_and_never_as_a_blank() -> None:
    """An unnamed term is a real state — its document is not readable from
    here — and printing the hash says so without pretending it does not exist."""
    dictionary = dictionary_mod.Dictionary()
    assert dictionary.name("deadbeefdeadbeef") == "deadbeefdeadbeef"
    dictionary.terms["deadbeefdeadbeef"] = "rank"
    assert dictionary.name("deadbeefdeadbeef") == "rank"
    dictionary.surfaces["deadbeefdeadbeef"] = "Ranking"
    assert dictionary.name("deadbeefdeadbeef") == "Ranking"


def test_the_dictionary_lands_under_runtime_which_is_gitignored(tmp_path) -> None:
    """Decision 3 and 15's whole claim, at the path level: `runtime/` is the
    one DERIVED child of `.fux/` and carries its own `.gitignore` line."""
    from fux.store import fuxdir

    directory = dictionary_mod.inspect_dir(tmp_path)
    assert directory == tmp_path / ".fux" / "runtime" / "inspect"
    assert "runtime" in fuxdir.DERIVED
