from __future__ import annotations

from fux.query.scan import ask, scan_candidates
from fux.store import term_hash, write_index


def _rec(doc_id, title, wlen, terms) -> dict:
    return {
        "id": doc_id,
        "src": "git",
        "loc": doc_id.removeprefix("file:"),
        "mode": "extracted",
        "meta": "plain",
        "title": title,
        "phrases": [],
        "terms": terms,
        "wlen": wlen,
        "edges": [],
    }


def test_empty_index_returns_nothing(tmp_path):
    assert ask(tmp_path, "anything") == []


def test_finds_a_matching_document(tmp_path):
    write_index(tmp_path, [_rec("file:a.md", "A", 10, {term_hash("pruning"): [0, 1]})])
    results = ask(tmp_path, "pruning")
    assert len(results) == 1
    assert results[0].id == "file:a.md"
    assert results[0].title == "A"
    assert results[0].loc == "a.md"
    assert results[0].score > 0


def test_query_with_no_matches_returns_empty(tmp_path):
    write_index(tmp_path, [_rec("file:a.md", "A", 10, {term_hash("pruning"): [0, 1]})])
    assert ask(tmp_path, "zzznomatch") == []


def test_heading_match_ranks_above_body_match(tmp_path):
    write_index(
        tmp_path,
        [
            _rec("file:heading.md", "Heading doc", 10, {term_hash("install"): [1, 0]}),
            _rec("file:body.md", "Body doc", 10, {term_hash("install"): [0, 1]}),
        ],
    )
    results = ask(tmp_path, "install")
    assert [r.id for r in results] == ["file:heading.md", "file:body.md"]


def test_deterministic_tiebreak_on_id(tmp_path):
    write_index(
        tmp_path,
        [
            _rec("file:b.md", "B", 10, {term_hash("same"): [0, 1]}),
            _rec("file:a.md", "A", 10, {term_hash("same"): [0, 1]}),
        ],
    )
    results = ask(tmp_path, "same")
    assert [r.id for r in results] == ["file:a.md", "file:b.md"]


def test_top_limits_results(tmp_path):
    write_index(
        tmp_path,
        [_rec(f"file:{i}.md", str(i), 10, {term_hash("x"): [0, 1]}) for i in range(10)],
    )
    assert len(ask(tmp_path, "x", top=3)) == 3


def test_multi_term_query_prefers_document_matching_both(tmp_path):
    write_index(
        tmp_path,
        [
            _rec("file:both.md", "Both", 10, {term_hash("pruning"): [0, 1], term_hash("gate"): [0, 1]}),
            _rec("file:one.md", "One", 10, {term_hash("pruning"): [0, 1]}),
        ],
    )
    results = ask(tmp_path, "pruning gate")
    assert results[0].id == "file:both.md"


def test_results_are_deterministic_across_repeated_calls(tmp_path):
    write_index(
        tmp_path,
        [_rec(f"file:{i}.md", str(i), 10 + i, {term_hash("pruning"): [i % 2, 1]}) for i in range(20)],
    )
    first = ask(tmp_path, "pruning")
    second = ask(tmp_path, "pruning")
    assert first == second


def test_df_is_not_inflated_by_a_hash_quoted_outside_terms(tmp_path):
    """A 16-hex term hash can appear quoted in a field other than `terms`
    (a title, an id, a sha) without that document actually containing the
    term. The substring prefilter that finds candidate lines is deliberately
    imprecise — that's the whole B2 speed trick — but `df` must not inherit
    that imprecision: it has to come from the parsed record's real `terms`
    keys, not from the raw substring match, or the accelerator (which is
    exact by construction) silently disagrees with this reference scan and
    derive/build.py's tripwire refuses to build.
    """
    stray_hash = term_hash("deadbeefdeadbeef")
    write_index(
        tmp_path,
        [
            # The hash string is literally quoted in `title`, not a key of `terms`.
            _rec("file:stray.md", stray_hash, 10, {}),
            _rec("file:real.md", "Real", 10, {stray_hash: [0, 1]}),
        ],
    )
    query_hashes = [stray_hash]
    candidates, df, corpus = scan_candidates(tmp_path, query_hashes)
    assert df[stray_hash] == 1  # only file:real.md actually has the term
    # Both lines matched the cheap substring prefilter (so both were parsed),
    # but only the real match should ever score above zero and be returned.
    assert {c["id"] for c in candidates} == {"file:stray.md", "file:real.md"}
    results = ask(tmp_path, "deadbeefdeadbeef")
    assert [r.id for r in results] == ["file:real.md"]


def test_scan_never_parses_non_candidate_lines(tmp_path, monkeypatch):
    """A line that can't match the query hash must never reach json.loads."""
    import fux.query.scan as scan_mod

    write_index(
        tmp_path,
        [
            _rec("file:match.md", "Match", 10, {term_hash("pruning"): [0, 1]}),
            _rec("file:nomatch.md", "NoMatch", 10, {term_hash("gate"): [0, 1]}),
        ],
    )
    real_loads = scan_mod.json.loads
    parsed_ids = []

    def spy(line):
        obj = real_loads(line)
        parsed_ids.append(obj.get("id"))
        return obj

    monkeypatch.setattr(scan_mod.json, "loads", spy)
    ask(tmp_path, "pruning")
    # `json.loads` is also called on each shard's header line internally (store/
    # reader.py's own header validation) — filter those (no "id" key) out and
    # check only that record-line parsing skipped the non-matching document.
    record_ids = [doc_id for doc_id in parsed_ids if doc_id is not None]
    assert record_ids == ["file:match.md"]
