"""`.fux/.fuxignore` — the grammar, the precedence, and the duplicate warning.

ADR-FUXIGNORE. Three properties carry the record, and each has its own block
below:

1. **The grammar is git's**, including the two rules people get wrong —
   *any* `/` anchors, and a file under an ignored directory cannot be
   re-included.
2. **It outranks the type allowlist in both directions.** An ignore beats an
   allow; an explicit `!` beats a *dis*allow. The second half is the one that
   changed a decided ADR, so it is pinned here rather than left to the walk.
3. **A pattern stated in two files warns and changes nothing.** The warning is
   early for the day someone edits one copy — `!` means opposite things in the
   two files.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.ingest import fuxignore
from fux.ingest.gitdir import read_types, source_dirs, source_excludes, walk_sources


# -- the grammar -----------------------------------------------------------


@pytest.mark.parametrize(
    "pattern,path,ignored",
    [
        # a bare name matches at any depth, either as a file or a directory
        ("build", "build", True),
        ("build", "a/b/build", True),
        ("node_modules", "x/node_modules/pkg/a.md", True),
        # a trailing slash means a DIRECTORY, and a file of that name survives
        ("build/", "build/x.md", True),
        ("build/", "a/build/x.md", True),
        ("build/", "build", False),
        # a leading slash anchors at the repo root
        ("/notes.md", "notes.md", True),
        ("/notes.md", "docs/notes.md", False),
        # ...and so does ANY other slash. This is the rule people get wrong.
        ("docs/build", "docs/build", True),
        ("docs/build", "a/docs/build", False),
        # `*` never crosses a slash; `**` is the explicit any-depth form
        ("*.log", "a/b/c.log", True),
        ("docs/*.md", "docs/deep/a.md", False),
        ("work/**/evidence", "work/a/b/evidence", True),
        ("work/**/evidence", "work/evidence", True),  # `**` matches zero dirs
        # character classes, negated ones included
        ("[0-9][0-9]-draft.md", "12-draft.md", True),
        ("[0-9][0-9]-draft.md", "ab-draft.md", False),
        ("[!0-9].md", "a.md", True),
        ("[!0-9].md", "1.md", False),
    ],
)
def test_git_glob_semantics(pattern, path, ignored):
    assert fuxignore.parse(pattern + "\n").decide(path).ignored is ignored


def test_last_match_wins_which_makes_order_semantic_here_and_nowhere_else():
    """Every other list fux reads is loader-sorted. This one is not, on purpose."""
    assert fuxignore.parse("*.log\n!keep.log\n").decide("keep.log").ignored is False
    assert fuxignore.parse("!keep.log\n*.log\n").decide("keep.log").ignored is True


def test_a_file_under_an_ignored_directory_cannot_be_re_included():
    """Git's rule, and the reason `.fux/**` + `!.fux/decoders/*.py` disappoints."""
    ignores = fuxignore.parse("build/\n!build/keep.md\n")
    assert ignores.decide("build/keep.md").ignored is True


def test_a_trailing_comment_after_whitespace_is_a_comment():
    """The one deliberate divergence from git, and it is the useful direction.

    Git reads `*.log   # noisy` as a literal pattern that matches nothing.
    """
    ignores = fuxignore.parse("*.log   # noisy\n")
    assert ignores.decide("a.log").ignored is True
    assert ignores.decide("a.log   # noisy").ignored is False


def test_a_full_line_comment_and_a_blank_line_are_not_rules():
    assert fuxignore.parse("# nothing here\n\n   \n").rules == ()


def test_an_absent_file_ignores_nothing(tmp_path):
    """Empty is legal here, unlike `types`: this file only ever subtracts."""
    ignores = fuxignore.read(tmp_path)
    assert not ignores
    assert ignores.decide("anything/at/all.md").rule is None


def test_a_bare_bang_is_a_loud_error():
    with pytest.raises(FuxError, match="no pattern after it"):
        fuxignore.parse("!\n")


def test_an_unmentioned_path_has_no_opinion_rather_than_a_re_include():
    """The distinction the allowlist override rests on.

    If "not ignored" and "explicitly re-included" were one state, an empty
    `.fuxignore` would index every file in the tree.
    """
    verdict = fuxignore.parse("*.log\n").decide("src/app.py")
    assert verdict.ignored is False
    assert verdict.reincluded is False


# -- precedence over the source lists --------------------------------------


def _corpus(tmp_path, *, types="*.md\n", dirs="docs\nsrc\n", ignore=None):
    (tmp_path / "docs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "docs/a.md").write_text("# A\n\nprose\n")
    (tmp_path / "docs/notes.log").write_text("log line\n")
    (tmp_path / "docs/empty.md").write_text("")
    (tmp_path / "src/app.py").write_text("print('x')\n")
    (tmp_path / ".fux/sources").mkdir(parents=True)
    (tmp_path / ".fux/sources/dirs").write_text(dirs)
    (tmp_path / ".fux/sources/types").write_text(types)
    if ignore is not None:
        (tmp_path / ".fux/.fuxignore").write_text(ignore)
    return tmp_path


def _walk(root):
    files, skipped = walk_sources(
        root,
        source_dirs(root, ".fux/sources/dirs"),
        excludes=source_excludes(root, ".fux/sources/dirs"),
        types=read_types(root, ".fux/sources/types"),
        ignores=fuxignore.read(root),
    )
    return [f.rel_path for f in files], {s.rel_path: s.reason for s in skipped}


def test_a_repo_with_no_fuxignore_walks_exactly_as_it_did_before(tmp_path):
    indexed, skipped = _walk(_corpus(tmp_path))
    assert indexed == ["docs/a.md"]
    assert skipped["docs/notes.log"] == "not an indexed file type"
    assert skipped["src/app.py"] == "not an indexed file type"


def test_an_ignore_beats_the_type_allowlist(tmp_path):
    indexed, skipped = _walk(_corpus(tmp_path, ignore="docs/a.md\n"))
    assert indexed == []
    assert "ignored by .fux/.fuxignore:1" in skipped["docs/a.md"]


def test_an_explicit_re_include_beats_the_type_allowlist(tmp_path):
    """ADR-FUXIGNORE decision 4's sharp half, and the one that moved ADR-TYPES.

    `.py` is in no allowlist and has no decoder. A `!` line indexes it anyway,
    as raw bytes — visible in one committed file, and only ever because someone
    wrote that line.
    """
    indexed, _ = _walk(_corpus(tmp_path, ignore="!*.py\n"))
    assert "src/app.py" in indexed


def test_a_re_included_file_is_still_skipped_when_there_is_nothing_to_read(tmp_path):
    """The content skips are not overridable, because overriding them buys nothing."""
    indexed, skipped = _walk(_corpus(tmp_path, ignore="!*.md\n"))
    assert "docs/empty.md" not in indexed
    assert skipped["docs/empty.md"] == "empty"


def test_the_skip_reason_names_the_file_the_line_and_the_pattern(tmp_path):
    """`--list-skipped` has to answer *why*, not just *which*."""
    _, skipped = _walk(_corpus(tmp_path, ignore="# a header\n*.log\n"))
    assert skipped["docs/notes.log"] == (
        "ignored by .fux/.fuxignore:2 `*.log` (docs/notes.log)"
    )


def test_an_ignored_directory_names_the_directory_not_the_file(tmp_path):
    root = _corpus(tmp_path, ignore="docs/\n")
    _, skipped = _walk(root)
    assert skipped["docs/a.md"].endswith("`docs/` (docs)")


def test_every_printed_reason_is_ascii(tmp_path):
    """These reach a Windows console (`tests/test_windows_console_safe.py`'s rule)."""
    _, skipped = _walk(_corpus(tmp_path, ignore="*.log\ndocs/\n"))
    for reason in skipped.values():
        reason.encode("ascii")


# -- the duplicate warning -------------------------------------------------


def _warnings(root):
    return fuxignore.duplicate_warnings(
        root, dirs_file=".fux/sources/dirs", types_file=".fux/sources/types"
    )


def test_a_pattern_in_both_files_warns_and_says_which_line_to_delete(tmp_path):
    root = _corpus(tmp_path, types="*.md\n!*.min.md\n", ignore="*.min.md\n")
    (warning,) = _warnings(root)
    assert "*.min.md" in warning
    assert ".fux/sources/types:2" in warning
    assert ".fux/.fuxignore:1" in warning
    assert "Delete `!*.min.md` from .fux/sources/types" in warning
    warning.encode("ascii")


def test_a_dirs_exclusion_repeated_in_fuxignore_warns_too(tmp_path):
    root = _corpus(tmp_path, dirs="docs\nsrc\n!docs/gen\n", ignore="docs/gen\n")
    (warning,) = _warnings(root)
    assert ".fux/sources/dirs:3" in warning


def test_a_negation_is_not_a_duplicate_of_an_exclusion_that_shares_its_spelling(tmp_path):
    """`!*.min.md` in `types` subtracts; `!*.min.md` here adds back.

    Same eight characters, opposite statements. Calling them duplicates would
    tell the reader to delete the line that is doing the opposite thing.
    """
    root = _corpus(tmp_path, types="*.md\n!*.min.md\n", ignore="!*.min.md\n")
    assert _warnings(root) == []


def test_no_fuxignore_means_no_warnings_however_many_exclusions_exist(tmp_path):
    assert _warnings(_corpus(tmp_path, types="*.md\n!*.min.md\n")) == []


# -- W-93: the fux-written blocks ------------------------------------------

BLOCKED = """\
# >>> fux: not indexed >>>
# blurb
a/b.py    # not an indexed file type
# <<< fux: not indexed <<<

# >>> fux: skipped >>>
c/d.md    # binary
# <<< fux: skipped <<<

*.log
!keep.log
"""


def test_a_block_line_is_a_literal_path_not_a_pattern():
    """`*` and `[` in a filename are characters, not globs.

    fux only ever writes exact repo-relative paths into a block, so translating
    them as globs would be inventing a meaning nothing put there.
    """
    ignores = fuxignore.parse(BLOCKED)
    assert set(ignores.generated) == {"a/b.py", "c/d.md"}
    assert [r.raw for r in ignores.rules] == ["*.log", "!keep.log"]


def test_the_block_a_line_sits_in_is_its_class():
    ignores = fuxignore.parse(BLOCKED)
    assert ignores.generated["a/b.py"].block == fuxignore.BLOCK_NOT_INDEXED
    assert ignores.generated["c/d.md"].block == fuxignore.BLOCK_SKIPPED


def test_a_generated_verdict_reports_the_reason_that_put_it_there():
    """Not *"ignored by .fuxignore:3"*.

    A block line is fux's own record of a verdict it already reached. Reporting
    the line as the reason would make the second run's answer *"because the
    first run said so"*, and the real reason would be lost after one ingest.
    """
    assert fuxignore.parse(BLOCKED).decide("a/b.py").reason() == "not an indexed file type"


def test_anything_you_write_outranks_anything_fux_generated():
    text = BLOCKED + "!a/b.py\n"
    assert fuxignore.parse(text).decide("a/b.py").reincluded


def test_hand_only_asks_what_the_file_would_say_with_the_blocks_deleted():
    ignores = fuxignore.parse(BLOCKED)
    assert ignores.decide("a/b.py").ignored
    assert not ignores.decide("a/b.py", hand_only=True).ignored
    assert ignores.decide("x/y.log", hand_only=True).ignored


def test_an_unclosed_block_swallows_the_rest_of_the_file():
    """`parse` and `_without_blocks` must agree, or a hand-written line could be
    read as a rule and then deleted as block content.
    """
    text = "# >>> fux: skipped >>>\na/b.md   # empty\n*.log\n"
    ignores = fuxignore.parse(text)
    assert ignores.rules == ()
    assert set(ignores.generated) == {"a/b.md", "*.log"}


def test_write_blocks_leaves_everything_outside_them_alone(tmp_path):
    target = tmp_path / fuxignore.IGNORE_FILE
    target.parent.mkdir(parents=True)
    target.write_text("# my header\n\n*.log\n!keep.log\n", encoding="utf-8")
    fuxignore.write_blocks(tmp_path, not_indexed=[("a/b.py", "why")], skipped=[])
    text = target.read_text(encoding="utf-8")
    assert text.endswith("# my header\n\n*.log\n!keep.log\n")
    assert text.index("# >>> fux") < text.index("!keep.log")


def test_write_blocks_is_idempotent_and_sorted(tmp_path):
    pairs = [("b.py", "why"), ("a.py", "why")]
    fuxignore.write_blocks(tmp_path, not_indexed=pairs, skipped=[])
    once = (tmp_path / fuxignore.IGNORE_FILE).read_text(encoding="utf-8")
    fuxignore.write_blocks(tmp_path, not_indexed=list(reversed(pairs)), skipped=[])
    assert (tmp_path / fuxignore.IGNORE_FILE).read_text(encoding="utf-8") == once
    assert once.index("a.py") < once.index("b.py")


def test_write_blocks_creates_nothing_when_there_is_nothing_to_record(tmp_path):
    fuxignore.write_blocks(tmp_path, not_indexed=[], skipped=[])
    assert not (tmp_path / fuxignore.IGNORE_FILE).exists()


def test_write_blocks_does_not_touch_an_unchanged_file(tmp_path):
    fuxignore.write_blocks(tmp_path, not_indexed=[("a.py", "why")], skipped=[])
    target = tmp_path / fuxignore.IGNORE_FILE
    before = target.stat().st_mtime_ns
    fuxignore.write_blocks(tmp_path, not_indexed=[("a.py", "why")], skipped=[])
    assert target.stat().st_mtime_ns == before, "an unchanged run must leave `git status` quiet"


def test_generated_lines_stay_out_of_the_duplicate_warning(tmp_path):
    """There can be hundreds of them, and they are paths nobody also writes
    into `sources/`. Including them would turn an advisory into a block scan.
    """
    assert fuxignore.parse(BLOCKED).patterns().keys() == {"*.log"}
