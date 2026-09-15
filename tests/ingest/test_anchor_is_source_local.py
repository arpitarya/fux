"""🔴 **The test W-168 step 1's ruling exists for.**

Arpit ruled option (c) on 2026-09-15 after the specified form of the feature
was found to break an invariant sharper than *"no cross-document
dependencies"*:

> **A committed per-document byte is a function of that document alone.
> Everything corpus-wide is a read-time fold.**

An `anchor` field on the TARGET, built from what everyone else calls it, would
have been the first thing in the engine to break it. Editing `B` would move
`A`'s committed bytes while [`maintain/runner.py`](../../src/fux/maintain/runner.py)
marked only `B` dirty, so a full `fux ingest` and an incremental re-index would
produce **different indexes from the same sources**.

⚠ **That failure would have been invisible here.** It is
[L3](../../records/0005_LAW-3-deterministic.md) failing on the *incremental*
path only — the full-ingest path stays byte-reproducible, so every test and
every CI check that rebuilds from scratch passes, and the drift appears only
in a working repository that has been edited over time. Nothing in this repo
would catch it. Hence a test on the property itself rather than on a symptom.

**If this ever goes red, the build has drifted back into option (a)** —
dirtying the out-edge targets — which Arpit refused here rather than deferred.
It is still probably owed, as its own `W-nn` under SR-MAINTENANCE sequenced
with `B-002`; it is not this item's, and nothing in W-168 waits on it.
"""

from __future__ import annotations

from fux import store
from fux.ingest.run import run


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


def _line_of(root, doc_id: str) -> bytes:
    """One document's committed line, as raw bytes."""
    path = store.shard_path(root, store.shard_for(doc_id))
    _, lines = store.raw_record_lines(path)
    needle = f'"id":"{doc_id}"'.encode("utf-8")
    matching = [line for line in lines if needle in line]
    assert len(matching) == 1, f"{doc_id} appears {len(matching)} times in {path}"
    return matching[0]


def test_edge_text_is_a_function_of_its_source_alone(tmp_path):
    """Edit the LINKER; the target's committed bytes must not move."""
    _init(
        tmp_path,
        {
            "docs/a.md": "# Alpha\n\nthe alpha document body\n",
            "docs/b.md": "# Beta\n\nSee [the alpha document](a.md).\n",
        },
    )
    run(tmp_path)
    a_before = _line_of(tmp_path, "file:docs/a.md")
    b_before = _line_of(tmp_path, "file:docs/b.md")

    # Only B changes, and only its LINK TEXT — the target is the same file.
    (tmp_path / "docs" / "b.md").write_text(
        "# Beta\n\nSee [the ranking runbook](a.md).\n", encoding="utf-8"
    )
    run(tmp_path)

    assert _line_of(tmp_path, "file:docs/a.md") == a_before, (
        "editing B moved A's committed bytes. The anchor words have drifted "
        "onto the TARGET's record, which is option (a) shipped under (c)'s "
        "name — and it breaks L3 on the incremental path, where nothing looks."
    )
    assert _line_of(tmp_path, "file:docs/b.md") != b_before, (
        "B's own anchor words did not change, so this test proved nothing. "
        "Check that the link text actually reaches the edge."
    )


def test_anchor_terms_are_not_in_the_targets_postings(tmp_path):
    """Saying so is part of the done-ness.

    It is what distinguishes (c) from the specified form: a build that quietly
    adds anchor terms to the target's `terms` has shipped (a) under (c)'s name,
    and would pass the test above while doing it.
    """
    _init(
        tmp_path,
        {
            "docs/a.md": "# Alpha\n\nthe alpha document body\n",
            "docs/b.md": "# Beta\n\nSee [the zarquon runbook](a.md).\n",
        },
    )
    run(tmp_path)
    index = store.read_index(tmp_path)
    assert store.term_hash("zarquon") not in index["file:docs/a.md"]["terms"], (
        "an anchor term reached the target's committed postings"
    )
    # ...and it IS on the linker's own edge, or the fixture proves nothing.
    (edge,) = [e for e in index["file:docs/b.md"]["edges"] if e["kind"] == "ref"]
    assert store.term_hash("zarquon") in edge["at"]


def test_the_targets_bytes_do_not_move_when_a_NEW_linker_appears(tmp_path):
    """The same invariant, from the other direction: adding a document that
    links to A must not rewrite A either."""
    _init(tmp_path, {"docs/a.md": "# Alpha\n\nthe alpha document body\n"})
    run(tmp_path)
    a_before = _line_of(tmp_path, "file:docs/a.md")

    (tmp_path / "docs" / "c.md").write_text(
        "# Gamma\n\nSee [the alpha document](a.md).\n", encoding="utf-8"
    )
    run(tmp_path)
    assert _line_of(tmp_path, "file:docs/a.md") == a_before
