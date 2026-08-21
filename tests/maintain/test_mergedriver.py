"""The merge driver's contract: never conflict on adjacency, never pick silently.

R6's unit half. The three-tier harness that measures the prediction end to end
lives in `tools/merge-harness/`; these are the properties that hold regardless
of what a repository does.
"""

from __future__ import annotations

import json

import pytest

from fux.maintain.mergedriver import MergeConflict, main, merge_shards

HEADER = '{"fux":"index","v":1}'


def _line(doc_id: str, ver: int = 1, sha: str = "aaa") -> str:
    return json.dumps({"id": doc_id, "ver": ver, "sha": sha}, sort_keys=True)


def _shard(*lines: str) -> str:
    return "\n".join([HEADER, *lines]) + "\n"


def _ids(text: str) -> list[str]:
    return [json.loads(l)["id"] for l in text.split("\n")[1:] if l.strip()]


# -- the reason the driver exists ------------------------------------------


def test_disjoint_adds_merge_to_the_union():
    """Two people documenting different things is not a disagreement."""
    base = _shard(_line("file:a.md"))
    ours = _shard(_line("file:a.md"), _line("file:b.md"))
    theirs = _shard(_line("file:a.md"), _line("file:c.md"))
    assert _ids(merge_shards(base, ours, theirs)) == ["file:a.md", "file:b.md", "file:c.md"]


def test_an_empty_ancestor_still_unions():
    """A shard created independently on both sides — the first-commit case."""
    merged = merge_shards("", _shard(_line("file:a.md")), _shard(_line("file:b.md")))
    assert _ids(merged) == ["file:a.md", "file:b.md"]


def test_output_is_sorted_by_id_whatever_the_input_order():
    ours = _shard(_line("file:z.md"), _line("file:a.md"))
    theirs = _shard(_line("file:m.md"))
    assert _ids(merge_shards("", ours, theirs)) == ["file:a.md", "file:m.md", "file:z.md"]


def test_merging_is_order_independent_and_therefore_deterministic():
    """Both sides' machines must produce the same bytes, or L3 has a hole."""
    base = _shard(_line("file:a.md"))
    ours = _shard(_line("file:a.md"), _line("file:b.md", ver=2))
    theirs = _shard(_line("file:a.md"), _line("file:c.md"))
    assert merge_shards(base, ours, theirs) == merge_shards(base, theirs, ours)


# -- last-writer-wins on (ver, sha) ----------------------------------------


def test_the_higher_ver_wins():
    base = _shard(_line("file:a.md", ver=1))
    ours = _shard(_line("file:a.md", ver=3, sha="ours"))
    theirs = _shard(_line("file:a.md", ver=2, sha="theirs"))
    merged = merge_shards(base, ours, theirs)
    assert json.loads(merged.split("\n")[1])["sha"] == "ours"
    # and symmetrically
    merged = merge_shards(base, theirs, ours)
    assert json.loads(merged.split("\n")[1])["sha"] == "ours"


def test_identical_records_are_not_a_conflict():
    line = _line("file:a.md", ver=4)
    assert _ids(merge_shards(_shard(_line("file:a.md")), _shard(line), _shard(line))) == ["file:a.md"]


def test_same_ver_different_bytes_is_refused():
    """One side ingested content the other did not have. Picking either lies."""
    base = _shard(_line("file:a.md", ver=1))
    with pytest.raises(MergeConflict) as exc:
        merge_shards(
            base,
            _shard(_line("file:a.md", ver=2, sha="ours")),
            _shard(_line("file:a.md", ver=2, sha="theirs")),
        )
    assert exc.value.ids == ["file:a.md"]


def test_both_added_the_same_id_differently_is_refused():
    with pytest.raises(MergeConflict):
        merge_shards("", _shard(_line("file:a.md", sha="x")), _shard(_line("file:a.md", sha="y")))


def test_a_side_unchanged_from_the_ancestor_never_blocks_the_other_sides_edit():
    """`ver` is how the common case is decided, not the only way it can be.

    If `ver` was not bumped on the changed side (a hand repair, an ingest
    edge case), comparing `ver` alone reads this as "same ver, different
    bytes" and refuses it — even though one side provably touched nothing.
    The fix compares against the ancestor first: a side byte-identical to
    `in_base` cannot be the one that changed, so the other side wins outright.
    """
    base = _shard(_line("file:a.md", ver=1, sha="orig"))
    ours = _shard(_line("file:a.md", ver=1, sha="orig"))               # untouched
    theirs = _shard(_line("file:a.md", ver=1, sha="changed"))          # edited, ver NOT bumped
    assert json.loads(merge_shards(base, ours, theirs).split("\n")[1])["sha"] == "changed"
    # and symmetrically
    assert json.loads(merge_shards(base, theirs, ours).split("\n")[1])["sha"] == "changed"


# -- deletions --------------------------------------------------------------


def test_a_deletion_beats_an_untouched_side():
    base = _shard(_line("file:a.md"), _line("file:b.md"))
    ours = _shard(_line("file:a.md"))                      # b deleted here
    theirs = _shard(_line("file:a.md"), _line("file:b.md"))
    assert _ids(merge_shards(base, ours, theirs)) == ["file:a.md"]


def test_both_deleted_is_agreement_not_conflict():
    base = _shard(_line("file:a.md"), _line("file:b.md"))
    side = _shard(_line("file:a.md"))
    assert _ids(merge_shards(base, side, side)) == ["file:a.md"]


def test_delete_versus_modify_is_refused():
    base = _shard(_line("file:a.md", ver=1))
    with pytest.raises(MergeConflict):
        merge_shards(base, _shard(), _shard(_line("file:a.md", ver=2, sha="changed")))


# -- the format itself ------------------------------------------------------


def test_a_header_change_is_never_auto_merged():
    """A format change is a decision, and the driver does not make decisions."""
    with pytest.raises(MergeConflict):
        merge_shards(
            _shard(_line("file:a.md")),
            '{"fux":"index","v":1}\n',
            '{"fux":"index","v":2}\n',
        )


def test_an_unparseable_line_refuses_rather_than_dropping_it():
    with pytest.raises(MergeConflict):
        merge_shards("", HEADER + "\nnot json\n", _shard(_line("file:a.md")))


# -- the CLI entry point git actually invokes ------------------------------


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_main_resolves_in_place_and_exits_zero(tmp_path):
    base = _write(tmp_path, "O", _shard(_line("file:a.md")))
    ours = _write(tmp_path, "A", _shard(_line("file:a.md"), _line("file:b.md")))
    theirs = _write(tmp_path, "B", _shard(_line("file:a.md"), _line("file:c.md")))
    assert main([str(base), str(ours), str(theirs)]) == 0
    # git reads the result out of %A — ours — so that is the file that changed.
    assert _ids(ours.read_text(encoding="utf-8")) == ["file:a.md", "file:b.md", "file:c.md"]


def test_main_leaves_conflict_markers_and_exits_nonzero(tmp_path, capsys):
    """The failure mode is 'refuse and leave both sides', never 'pick one'."""
    base = _write(tmp_path, "O", _shard(_line("file:a.md", ver=1)))
    ours = _write(tmp_path, "A", _shard(_line("file:a.md", ver=2, sha="ours")))
    theirs = _write(tmp_path, "B", _shard(_line("file:a.md", ver=2, sha="theirs")))
    assert main([str(base), str(ours), str(theirs)]) != 0
    text = ours.read_text(encoding="utf-8")
    assert "<<<<<<< ours" in text and ">>>>>>> theirs" in text
    assert "ours" in text and "theirs" in text          # both sides survive
    assert "file:a.md" in capsys.readouterr().err


def test_main_with_a_missing_ancestor_is_the_add_add_case(tmp_path):
    ours = _write(tmp_path, "A", _shard(_line("file:a.md")))
    theirs = _write(tmp_path, "B", _shard(_line("file:b.md")))
    assert main([str(tmp_path / "absent"), str(ours), str(theirs)]) == 0
    assert _ids(ours.read_text(encoding="utf-8")) == ["file:a.md", "file:b.md"]


def test_main_without_three_arguments_is_a_usage_error(tmp_path):
    assert main([str(tmp_path)]) == 2


def test_crlf_input_merges_and_output_is_lf_only(tmp_path):
    """A file checked out with CRLF (Windows) must not corrupt the merge, and
    the result must be LF-only regardless of host OS — L3's byte-identical
    guarantee has no OS exception.
    """
    crlf_shard = _shard(_line("file:a.md"), _line("file:b.md")).replace("\n", "\r\n")
    base = tmp_path / "O"
    base.write_bytes(_shard(_line("file:a.md")).encode("utf-8"))
    ours = tmp_path / "A"
    ours.write_bytes(crlf_shard.encode("utf-8"))
    theirs = tmp_path / "B"
    theirs.write_bytes(_shard(_line("file:a.md"), _line("file:c.md")).encode("utf-8"))

    assert main([str(base), str(ours), str(theirs)]) == 0
    raw = ours.read_bytes()
    assert b"\r" not in raw
    assert _ids(raw.decode("utf-8")) == ["file:a.md", "file:b.md", "file:c.md"]
