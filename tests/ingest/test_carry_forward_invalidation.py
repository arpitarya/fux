"""W-166 — the three ways a carried-forward record silently kept stale bytes.

Ingest reuses a document's extracted record when its source bytes are unchanged.
The reuse key carried the PII ruleset digest and the `[index]` caps; **two other
inputs to extraction were not in it**, each named in its own record as stated
rather than fixed:

- a **decoder** change reached an unchanged document only on `--full`
  ([SR-DECODE](../../records/0139_decode.md) decision 11a: *"There is no decoder
  digest. Stated, not fixed."*)
- an **extraction rule** change, the same
  ([SR-INGEST](../../records/0106_ingest.md) Consequences)

The shape of the failure is what makes it worth a file of its own: ingest
reports success, the index holds text the current code would not produce, and
nothing on any surface says so.

**The keep test is the no-op delta** (`test_a_no_op_delta_re_extracts_nothing`):
a digest too coarse turns every engine release into a full re-ingest of every
consumer's repo, which is the failure mode W-166 was told to measure before
shipping.
"""

from __future__ import annotations

import pytest

from fux.ingest import decoderdigest
from fux.ingest.run import run

CSV = "name,role\nada,engineer\ngrace,admiral\n"
MD = "---\ntitle: Handbook\n---\n\n# Handbook\n\nthe oncall rota and the pager.\n"


def _init(tmp_path):
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    (tmp_path / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    # SR-PII decision 17: a repo without .fux/pii.toml refuses; empty redacts nothing.
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    return tmp_path


@pytest.fixture
def mixed(tmp_path):
    """A corpus with a decoded type and a prose type, so a blast radius is visible."""
    _init(tmp_path)
    (tmp_path / "docs" / "people.csv").write_text(CSV, encoding="utf-8")
    (tmp_path / "docs" / "handbook.md").write_text(MD, encoding="utf-8")
    run(tmp_path)
    return tmp_path


# -- the keep test ----------------------------------------------------------


def test_a_no_op_delta_re_extracts_nothing(mixed):
    """🔴 **The keep/remove call for the whole item.**

    A digest too coarse makes a routine engine release re-ingest every corpus. If
    this ever goes red, the decoder digest is scoped wrong and the item is
    re-measured before it ships — it is not adjudicated by loosening the test.
    """
    report = run(mixed)
    assert report.changed_count == 0
    assert report.reused_count == 2


def test_a_second_no_op_delta_also_re_extracts_nothing(mixed):
    """Twice, because a digest written in the wrong place converges on run two."""
    run(mixed)
    assert run(mixed).changed_count == 0


# -- 1. the decoder digest --------------------------------------------------


def test_a_decoder_bump_re_extracts_exactly_its_bindings(mixed, monkeypatch):
    """The design claim: `.csv` re-extracts, the markdown beside it does not."""
    import fux.decode.csv as csv_mod

    monkeypatch.setattr(csv_mod, "VERSION", csv_mod.VERSION + 1)
    report = run(mixed)
    # ⚠ **`reused_count`, not `changed_count`.** `changed` counts documents whose
    # SHA moved, and a decoder bump moves no source byte — so the natural-looking
    # assertion is green on a broken reuse key and on a fixed one alike. The
    # number that says what the key did is how many records it carried forward.
    assert report.reused_count == 1  # handbook.md, untouched
    assert report.doc_count - report.reused_count == 1  # people.csv, re-extracted


def test_a_decoder_bump_for_a_format_the_corpus_lacks_changes_nothing(mixed, monkeypatch):
    """A `.pptx` fix must not re-extract a corpus with no slides in it."""
    import fux.decode.pptx as pptx_mod

    monkeypatch.setattr(pptx_mod, "VERSION", pptx_mod.VERSION + 1)
    assert run(mixed).reused_count == 2


def test_a_consumer_decoder_appearing_re_extracts_that_extension(mixed):
    """⚠ **Appearing counts as a move**, not only changing.

    Dropping in a decoder changes how its files are read, which is as much a
    change to what the index holds as editing one.
    """
    decoders = mixed / ".fux" / "decoders"
    decoders.mkdir(parents=True)
    (decoders / "csv.py").write_text(
        'EXTENSIONS = (".csv",)\n\n\ndef decode(raw, rel_path):\n'
        '    return "# people\\n\\nconsumer decoded\\n"\n',
        encoding="utf-8",
    )
    report = run(mixed)
    assert report.reused_count == 1
    assert report.doc_count - report.reused_count == 1


def test_a_consumer_decoder_disappearing_re_extracts_too(mixed):
    """The other direction, and the one a presence-keyed check would miss."""
    decoders = mixed / ".fux" / "decoders"
    decoders.mkdir(parents=True)
    (decoders / "csv.py").write_text(
        'EXTENSIONS = (".csv",)\n\n\ndef decode(raw, rel_path):\n'
        '    return "# people\\n\\nconsumer decoded\\n"\n',
        encoding="utf-8",
    )
    run(mixed)
    assert run(mixed).reused_count == 2  # settled

    (decoders / "csv.py").unlink()
    assert run(mixed).reused_count == 1


def test_editing_a_consumer_decoder_re_extracts_it(mixed):
    """A consumer decoder is digested by its bytes — no constant to forget."""
    decoders = mixed / ".fux" / "decoders"
    decoders.mkdir(parents=True)
    path = decoders / "csv.py"
    path.write_text(
        'EXTENSIONS = (".csv",)\n\n\ndef decode(raw, rel_path):\n    return "# a\\n\\none\\n"\n',
        encoding="utf-8",
    )
    run(mixed)
    assert run(mixed).reused_count == 2

    path.write_text(
        'EXTENSIONS = (".csv",)\n\n\ndef decode(raw, rel_path):\n    return "# a\\n\\ntwo\\n"\n',
        encoding="utf-8",
    )
    assert run(mixed).reused_count == 1


def test_the_new_text_actually_reaches_the_index(mixed):
    """The point of all of it — the terms move, not just the counter.

    A re-extraction that produced the same record would satisfy every count
    above and fix nothing.
    """
    from fux.store import read_index

    decoders = mixed / ".fux" / "decoders"
    decoders.mkdir(parents=True)
    (decoders / "csv.py").write_text(
        'EXTENSIONS = (".csv",)\n\n\ndef decode(raw, rel_path):\n'
        '    return "# people\\n\\nzarquon zarquon\\n"\n',
        encoding="utf-8",
    )
    run(mixed)
    record = read_index(mixed)["file:docs/people.csv"]
    assert record["title"] == "people"
    # `ada` came from the built-in decoder's table; the consumer's does not emit it.
    assert "ada" not in str(record)


# -- 2. the extraction-rule digest ------------------------------------------


def test_an_extraction_rule_bump_re_extracts_the_whole_corpus(mixed, monkeypatch):
    """⚠ **Corpus-wide, deliberately.** These rules run on every document.

    There is no smaller set to invalidate, which is exactly why it is a constant
    somebody bumps rather than a sha of the module — a whitespace edit would
    otherwise charge a full re-extraction.
    """
    from fux.ingest import extract as extract_mod

    monkeypatch.setattr(extract_mod, "RULES_VERSION", extract_mod.RULES_VERSION + 1)
    report = run(mixed)
    assert report.reused_count == 0
    assert report.doc_count == 2  # both re-extracted


# -- determinism (L3) -------------------------------------------------------


def test_a_delta_run_is_still_byte_identical_to_a_full_run(mixed, monkeypatch):
    """The property every reuse change has to keep, checked across a bump.

    Same sources -> same index, whichever path got there. A reuse key that let a
    stale record through would show up here and nowhere else.
    """
    import fux.decode.csv as csv_mod
    from fux.store import iter_shard_paths

    def digest():
        import hashlib

        h = hashlib.sha256()
        for path in sorted(iter_shard_paths(mixed)):
            h.update(path.read_bytes())
        return h.hexdigest()

    monkeypatch.setattr(csv_mod, "VERSION", csv_mod.VERSION + 1)
    run(mixed)
    after_delta = digest()
    run(mixed, full=True)
    assert digest() == after_delta


def test_the_digests_are_not_functions_of_time(mixed):
    """L3: the same tree gives the same key, so two clean runs agree."""
    first = decoderdigest.binding_digests(mixed)
    second = decoderdigest.binding_digests(mixed)
    assert first == second
    assert all(":" not in v or v.split(":")[0].endswith("@sha") for v in first.values())
