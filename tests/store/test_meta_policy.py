"""L5 at write time — no path into a committed shard can leak display text.

The enforcement moved out of `ingest/run.py` and into `write_index` in M5. The
point of the move is the tests at the foot of this file: they try to get a
leaking record into a shard by every route that exists, and every route fails.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.store.reader import read_index
from fux.store.writer import assert_meta_policy, write_index


def _git(doc_id="file:a.md", **extra) -> dict:
    return {"id": doc_id, "src": "git", "loc": "a.md", "mode": "extracted", **extra}


def _url(doc_id="url:https://x/1", **extra) -> dict:
    return {"id": doc_id, "src": "url", "loc": "https://x/1", "mode": "extracted", **extra}


# -- git sources are exempt, and that is the whole asymmetry ---------------


def test_a_git_record_may_carry_a_title(tmp_path):
    """The repo already holds the bytes; hashing its title protects nothing."""
    write_index(tmp_path, [_git(title="A", phrases=["a b"])])
    assert read_index(tmp_path)["file:a.md"]["title"] == "A"


def test_a_git_record_needs_no_meta_at_all(tmp_path):
    assert_meta_policy(_git())


# -- non-git records must say what they are --------------------------------


def test_a_non_git_record_without_meta_is_refused(tmp_path):
    """Absence means the policy layer was bypassed. Guessing is the leak."""
    with pytest.raises(FuxError, match="must state `meta` explicitly"):
        write_index(tmp_path, [_url(title_h="abc")])


def test_an_unknown_meta_value_is_refused(tmp_path):
    with pytest.raises(FuxError, match="meta must be 'plain' or 'hashed'"):
        write_index(tmp_path, [_url(meta="secret", title_h="abc")])


@pytest.mark.parametrize("field", ["title", "phrases"])
def test_hashed_plus_display_text_is_refused(tmp_path, field):
    """The ACL-mismatch leak, named: fifty readers in Confluence, everyone in git."""
    record = _url(meta="hashed", title_h="abc", **{field: "leaked" if field == "title" else ["leaked"]})
    with pytest.raises(FuxError, match="ACL-mismatch leak"):
        write_index(tmp_path, [record])


def test_hashed_without_a_title_hash_is_refused(tmp_path):
    with pytest.raises(FuxError, match="no `title_h`"):
        write_index(tmp_path, [_url(meta="hashed")])


def test_hashed_and_clean_is_written(tmp_path):
    write_index(tmp_path, [_url(meta="hashed", title_h="abc")])
    assert read_index(tmp_path)["url:https://x/1"]["title_h"] == "abc"


def test_plain_is_a_legal_explicit_opt_out(tmp_path):
    """ADR-URL-LIST decision 10 — it is allowed, but it has to be *said*."""
    write_index(tmp_path, [_url(meta="plain", title="Public page")])
    assert read_index(tmp_path)["url:https://x/1"]["title"] == "Public page"


# -- the bypass attempts ----------------------------------------------------


def test_nothing_is_written_when_one_record_in_a_batch_leaks(tmp_path):
    """The check runs before the first byte lands, so a batch is all-or-nothing."""
    with pytest.raises(FuxError):
        write_index(tmp_path, [_git(title="fine"), _url(meta="hashed", title="leak", title_h="a")])
    assert not (tmp_path / ".fux" / "index").exists()


def test_the_leak_cannot_be_smuggled_past_by_a_second_writer(tmp_path):
    """A migration script, an enrichment pass, a fixture — same door, same lock.

    This is the test the move exists for. Before M5 the check lived in
    `ingest/run.py`, so any caller that did not go through ingest wrote
    whatever it liked into a committed shard.
    """
    write_index(tmp_path, [_url(meta="hashed", title_h="abc")])       # a clean index
    with pytest.raises(FuxError, match="ACL-mismatch leak"):
        write_index(tmp_path, [_url(meta="hashed", title_h="abc", title="now with a title")])
    assert "title" not in read_index(tmp_path)["url:https://x/1"]


def test_src_absent_is_treated_as_non_git(tmp_path):
    """Fail closed: an unlabelled record does not get the git exemption."""
    with pytest.raises(FuxError, match="must state `meta` explicitly"):
        write_index(tmp_path, [{"id": "url:x", "loc": "x", "mode": "extracted"}])
