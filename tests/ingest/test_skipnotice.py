"""The skip record — W-88 (report once) and W-93 (it lives in `.fuxignore`).

Two properties under test, and they pull against each other, which is why both
are here:

- **Suppression without loss** — every skip reaches the console the first time
  it is seen, a skip whose reason changes reaches it again, and nothing about
  the committed index moves either way.
- **The record is `.fux/.fuxignore`, and it DECIDES.** Arpit ruled on
  2026-08-27 that the list belongs in a committed file rather than
  `.fux/runtime/skipped`. A line there is a real ignore, so the tests pin the
  cost of that as carefully as the benefit: the escape hatches, the freeze, and
  the warning that makes a frozen-and-now-wrong line loud.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from fux.ingest import cmd_ingest, fuxignore, ingest_and_report, skipnotice
from fux.ingest.gitdir import Skipped, read_types, source_excludes
from fux.store import iter_shard_paths


def _init(tmp_path) -> None:
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (tmp_path / "docs").mkdir(exist_ok=True)


@pytest.fixture
def corpus(tmp_path):
    """One indexable document and three that are skipped, for one reason."""
    _init(tmp_path)
    docs = tmp_path / "docs"
    (docs / "real.md").write_text("---\ntitle: Real\n---\n\n# Real\n\nwidget\n", encoding="utf-8")
    (docs / "empty.md").write_text("", encoding="utf-8")
    (docs / "also-empty.md").write_text("", encoding="utf-8")
    (docs / "third-empty.md").write_text("", encoding="utf-8")
    return tmp_path


def _args():
    return SimpleNamespace(full=False, progress=None, no_accelerator=True)


def _skips(captured: str) -> list[str]:
    return [line for line in captured.splitlines() if line.startswith("  skip ")]


def _summary(captured: str) -> str:
    return next(line for line in captured.splitlines() if line.startswith("ingested "))


def _digest(root) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in iter_shard_paths(root)}


def _typed(root) -> None:
    """Narrow the allowlist to `*.md` so a `.py` file is a POLICY skip."""
    types = root / ".fux" / "sources" / "types"
    types.parent.mkdir(parents=True, exist_ok=True)
    types.write_text("*.md\n", encoding="utf-8")


def _ignore_text(root) -> str:
    return skipnotice.path(root).read_text(encoding="utf-8")


# -- report once, which is W-88 and still holds ----------------------------


def test_the_first_run_reports_every_skip(corpus, capsys):
    ingest_and_report(corpus, _args())
    assert len(_skips(capsys.readouterr().out)) == 3


def test_the_second_run_reports_none_of_them_and_says_so(corpus, capsys):
    ingest_and_report(corpus, _args())
    capsys.readouterr()
    ingest_and_report(corpus, _args())
    out = capsys.readouterr().out
    assert _skips(out) == []
    assert "3 already recorded in" in out
    assert "--list-skipped" in out


def test_a_new_skip_is_reported_and_the_rest_are_counted(corpus, capsys):
    ingest_and_report(corpus, _args())
    capsys.readouterr()
    (corpus / "docs" / "late.md").write_text("", encoding="utf-8")
    ingest_and_report(corpus, _args())
    out = capsys.readouterr().out
    assert _skips(out) == ["  skip docs/late.md: empty"]
    assert "3 more already recorded in" in out


def test_a_changed_reason_is_news_again(corpus):
    ingest_and_report(corpus, _args())
    skipnotice.write(corpus, [Skipped("docs/empty.md", "not an indexed file type")])
    assert skipnotice.unseen(corpus, [Skipped("docs/empty.md", "empty")]) != []


def test_a_pattern_you_wrote_is_not_news_either(corpus, capsys):
    """The wall W-88 removed, rebuilt by W-93 if this is missing.

    A path a hand-written pattern covers gets **no** generated line — one line
    beats many — so nothing records it, and without this rule it would print on
    every single run forever.
    """
    ingest_and_report(corpus, _args())
    skipnotice.path(corpus).write_text("*.md\n", encoding="utf-8")
    capsys.readouterr()
    ingest_and_report(corpus, _args())
    ingest_and_report(corpus, _args())
    assert _skips(capsys.readouterr().out) == []


def test_suppression_never_moves_a_committed_index_byte(corpus):
    ingest_and_report(corpus, _args())
    before = _digest(corpus)
    ingest_and_report(corpus, _args())
    assert _digest(corpus) == before


# -- W-93: the record is .fuxignore, it is committed, and it decides -------


def test_the_record_is_fuxignore_and_nothing_lands_under_runtime(corpus):
    ingest_and_report(corpus, _args())
    assert skipnotice.path(corpus) == corpus / fuxignore.IGNORE_FILE
    assert skipnotice.path(corpus).is_file()
    assert not skipnotice.legacy_path(corpus).exists()


def test_a_legacy_runtime_notice_is_deleted_on_the_next_run(corpus):
    """A repo carrying `.fux/runtime/skipped` from an older fux loses it.

    Two files answering one question is what this change removed; leaving the
    old one behind would keep a second, stale answer on disk forever.
    """
    legacy = skipnotice.legacy_path(corpus)
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("docs/gone.md: empty\n", encoding="utf-8")
    ingest_and_report(corpus, _args())
    assert not legacy.exists()


def test_the_two_blocks_carry_the_class_structurally(corpus):
    """Which block a line is in **is** its class — never parsed from the note."""
    _typed(corpus)
    (corpus / "docs" / "tool.py").write_text("x = 1\n", encoding="utf-8")
    ingest_and_report(corpus, _args())
    generated = fuxignore.read(corpus).generated
    assert generated["docs/tool.py"].block == fuxignore.BLOCK_NOT_INDEXED
    assert generated["docs/empty.md"].block == fuxignore.BLOCK_SKIPPED


def test_the_counts_survive_the_round_trip(corpus, capsys):
    """Run 2 reads its own record back and must report what run 1 found.

    The line carries the reason that put it there, so the answer never decays
    into *"because `.fuxignore` says so"* — which is what would happen if the
    generated verdict reported itself.
    """
    _typed(corpus)
    (corpus / "docs" / "tool.py").write_text("x = 1\n", encoding="utf-8")
    ingest_and_report(corpus, _args())
    first = _summary(capsys.readouterr().out)
    ingest_and_report(corpus, _args())
    second = _summary(capsys.readouterr().out)
    counts = "1 not indexed, 3 skipped,"
    assert counts in first and counts in second


def test_the_block_is_byte_stable_after_the_first_run(corpus):
    """L3: same corpus, same bytes. A committed file may not churn."""
    ingest_and_report(corpus, _args())
    after_first = _ignore_text(corpus)
    ingest_and_report(corpus, _args())
    ingest_and_report(corpus, _args())
    assert _ignore_text(corpus) == after_first


def test_the_block_carries_no_wall_clock(corpus):
    ingest_and_report(corpus, _args())
    body = [ln for ln in _ignore_text(corpus).splitlines() if not ln.startswith("#")]
    assert [ln for ln in body if ln.strip()] == [
        "docs/also-empty.md    # empty",
        "docs/empty.md         # empty",
        "docs/third-empty.md   # empty",
    ]


def test_the_blocks_are_written_above_everything_you_wrote(corpus):
    """Last match wins in this file, so a block written last would beat a `!`
    line you wrote. First means you always win — the one hazard of letting a
    machine edit a `.gitignore`-shaped file, closed by ordering.
    """
    skipnotice.path(corpus).write_text("# mine\n!docs/empty.md\n", encoding="utf-8")
    ingest_and_report(corpus, _args())
    text = _ignore_text(corpus)
    assert text.startswith("# >>> fux")
    assert text.index("# >>> fux") < text.index("!docs/empty.md")


def test_a_bang_line_you_wrote_beats_a_generated_line(corpus, capsys):
    ingest_and_report(corpus, _args())
    with skipnotice.path(corpus).open("a", encoding="utf-8") as fh:
        fh.write("\n!docs/empty.md\n")
    (corpus / "docs" / "empty.md").write_text("---\ntitle: Back\n---\n\nwidget\n", encoding="utf-8")
    capsys.readouterr()
    ingest_and_report(corpus, _args())
    assert "ingested 2 docs" in _summary(capsys.readouterr().out)


def test_deleting_a_line_indexes_the_document_again(corpus, capsys):
    """The escape hatch, and the whole reason the freeze is survivable."""
    ingest_and_report(corpus, _args())
    (corpus / "docs" / "empty.md").write_text("---\ntitle: Back\n---\n\nwidget\n", encoding="utf-8")
    text = "\n".join(
        ln for ln in _ignore_text(corpus).splitlines() if not ln.startswith("docs/empty.md")
    )
    skipnotice.path(corpus).write_text(text + "\n", encoding="utf-8")
    capsys.readouterr()
    ingest_and_report(corpus, _args())
    assert "ingested 2 docs" in _summary(capsys.readouterr().out)


def test_a_hand_written_pattern_collapses_many_generated_lines(corpus):
    """Write `*.md` yourself and three generated lines become none."""
    ingest_and_report(corpus, _args())
    assert len(fuxignore.read(corpus).generated) == 3
    skipnotice.path(corpus).write_text("*.md\n", encoding="utf-8")
    ingest_and_report(corpus, _args())
    assert fuxignore.read(corpus).generated == {}


def test_the_last_skip_going_away_empties_the_blocks(corpus):
    ingest_and_report(corpus, _args())
    assert fuxignore.read(corpus).generated
    for name in ("empty.md", "also-empty.md", "third-empty.md"):
        (corpus / "docs" / name).unlink()
    ingest_and_report(corpus, _args())
    assert fuxignore.read(corpus).generated == {}
    assert "# >>> fux" not in _ignore_text(corpus)


def test_a_url_never_reaches_a_block(corpus):
    """`.fuxignore` matches repo-relative paths; an `https://` line there would
    ignore nothing while reading as though it did.
    """
    skipnotice.write(corpus, [Skipped("https://example.com/a", "fetch failed: timeout")])
    assert fuxignore.read(corpus).generated == {}


@pytest.mark.parametrize("bad", ["docs/a #b.md", " docs/a.md", "docs/a.md ", "docs/a\nb.md"])
def test_a_path_that_cannot_round_trip_is_refused_not_mangled(bad):
    """Silently writing a line that parses back as a different path would
    ignore the wrong file. A refused path keeps being reported instead.
    """
    assert not fuxignore.writable(bad)


# -- the freeze, and the warning that keeps it from being silent ----------


def test_a_frozen_line_that_stopped_being_true_warns_loudly(corpus, capsys):
    """The cost of a committed record: the line decides, so it freezes.

    Arpit's call on 2026-08-27, and not undone here — made loud instead. A
    frozen line that is also wrong is an invisible filter, which is the failure
    ADR-FUXIGNORE exists to abolish.
    """
    ingest_and_report(corpus, _args())
    capsys.readouterr()
    (corpus / "docs" / "empty.md").write_text("---\ntitle: Back\n---\n\nwidget\n", encoding="utf-8")
    ingest_and_report(corpus, _args())
    err = capsys.readouterr().err
    assert "docs/empty.md" in err and "no longer true" in err
    assert "Delete it to index the document." in err


def test_the_warning_is_stderr_so_a_piped_ingest_is_unchanged(corpus, capsys):
    ingest_and_report(corpus, _args())
    capsys.readouterr()
    (corpus / "docs" / "empty.md").write_text("---\ntitle: Back\n---\n\nwidget\n", encoding="utf-8")
    ingest_and_report(corpus, _args())
    captured = capsys.readouterr()
    assert "no longer true" in captured.err
    assert "no longer true" not in captured.out


def test_nothing_warns_while_every_line_is_still_true(corpus, capsys):
    ingest_and_report(corpus, _args())
    capsys.readouterr()
    ingest_and_report(corpus, _args())
    assert "no longer true" not in capsys.readouterr().err


def test_a_line_your_own_pattern_also_covers_never_warns(corpus, capsys):
    """The generated line is not what holds the file out, so it is not fux's
    claim to be wrong about.
    """
    ingest_and_report(corpus, _args())
    with skipnotice.path(corpus).open("a", encoding="utf-8") as fh:
        fh.write("\n*.md\n")
    (corpus / "docs" / "empty.md").write_text("---\ntitle: Back\n---\n\nwidget\n", encoding="utf-8")
    capsys.readouterr()
    ingest_and_report(corpus, _args())
    assert "no longer true" not in capsys.readouterr().err


def test_stale_warnings_read_bytes_only_for_a_path_that_passed_both_lists(corpus):
    """The check is cheap on the population that is large: a `.py` file fails
    the allowlist and is never opened.
    """
    _typed(corpus)
    (corpus / "docs" / "tool.py").write_text("x = 1\n", encoding="utf-8")
    ingest_and_report(corpus, _args())
    opened: list[str] = []
    original = type(corpus).read_bytes

    def spy(self):
        opened.append(self.name)
        return original(self)

    type(corpus).read_bytes = spy
    try:
        skipnotice.stale_warnings(
            corpus,
            types=read_types(corpus),
            excludes=source_excludes(corpus, ".fux/sources/dirs"),
        )
    finally:
        type(corpus).read_bytes = original
    assert "tool.py" not in opened


# -- the machine-readable twin is unchanged -------------------------------


def test_list_skipped_output_is_unprefixed_and_sorted(corpus, capsys, monkeypatch):
    """`--list-skipped` is what things pipe; the wording change belongs to the
    human summary only.
    """
    _typed(corpus)
    (corpus / "docs" / "tool.py").write_text("x = 1\n", encoding="utf-8")
    ingest_and_report(corpus, _args())
    capsys.readouterr()
    monkeypatch.chdir(corpus)
    cmd_ingest(SimpleNamespace(list_skipped=True))
    listed = capsys.readouterr().out.splitlines()
    assert listed == sorted(listed)
    assert listed == [
        "docs/also-empty.md: empty",
        "docs/empty.md: empty",
        "docs/third-empty.md: empty",
        "docs/tool.py: not an indexed file type",
    ]
