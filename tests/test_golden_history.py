"""`tools/golden-history/replay.py` — W-168 step 8's instrument (test-data item T11).

**The property that matters most is the first test:** with no history, the plan
is the ladder's old one, commit for commit, message for message. A rung rebuilt
by the new builder with an empty `seed-history.tsv` must not move, or every
number filed against the old ladder is compared with a different corpus.

⚠ **Stdlib + git only.** It reads `work/golden/seed-dates.tsv` by name and
nothing else under `work/golden/` — never a question file, never a key.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SEED_DATES = ROOT / "work" / "golden" / "seed-dates.tsv"


def _load():
    spec = importlib.util.spec_from_file_location(
        "golden_history_replay", ROOT / "tools" / "golden-history" / "replay.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their module by name
    spec.loader.exec_module(module)
    return module


replay = _load()

PRIYA = "Priya Nair <priya@quillfern.example>"
TOMASZ = "Tomasz Kral <tomasz@quillfern.example>"


def _seed_dates() -> dict[str, str]:
    out = {}
    for line in SEED_DATES.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            path, date = line.split("\t")
            out[path.strip()] = date.strip()
    return out


def _rev(path, date, author, source):
    return replay.Revision(path, date, author, source)


# -- no history: the old ladder, exactly ------------------------------------


def test_no_history_is_the_old_ladder_commit_for_commit():
    """The builder before this file: group by date, sorted, one author, and the
    message `corpus: <date> (<n> documents)`."""
    dates = _seed_dates()
    assert dates, "seed-dates.tsv is empty — nothing to compare"
    old: dict[str, list[str]] = defaultdict(list)
    for path, date in dates.items():
        old[date].append(path)
    expected = [(d, sorted(old[d]), f"corpus: {d} ({len(old[d])} documents)") for d in sorted(old)]

    commits = replay.plan(dates, [])
    got = [(c.date, [r.path for r in c.revisions], c.message) for c in commits]
    assert got == expected
    assert {c.author for c in commits} == {replay.DEFAULT_AUTHOR}


def test_an_absent_history_file_is_no_history(tmp_path):
    assert replay.read_history(tmp_path / "seed-history.tsv") == []


# -- with history -----------------------------------------------------------


def test_history_splits_commits_by_author_and_keeps_the_final_date():
    dates = {"seed/a.md": "2024-09-03", "seed/b.md": "2024-09-03"}
    history = [
        _rev("seed/a.md", "2024-02-01", PRIYA, "seed-history/a.md@1"),
        _rev("seed/a.md", "2024-05-10", TOMASZ, "seed-history/a.md@2"),
        _rev("seed/a.md", "2024-09-03", PRIYA, "final"),
    ]
    commits = replay.plan(dates, history)
    assert [(c.date, c.author, [r.path for r in c.revisions]) for c in commits] == [
        ("2024-02-01", PRIYA, ["seed/a.md"]),
        ("2024-05-10", TOMASZ, ["seed/a.md"]),
        ("2024-09-03", PRIYA, ["seed/a.md"]),
        ("2024-09-03", replay.DEFAULT_AUTHOR, ["seed/b.md"]),
    ]
    assert commits[0].message == "corpus: 2024-02-01 · Priya Nair (1 documents)"
    assert replay.census(commits) == {
        "documents_with_history": 1,
        "history_commits": 3,
        "history_authors": 2,
        "max_authors_per_document": 2,
    }


@pytest.mark.parametrize(
    "rows, fragment",
    [
        ([("2024-02-01", "seed-history/a.md@1")], "0 `final` rows"),
        ([("2024-02-01", "final"), ("2024-09-03", "final")], "2 `final` rows"),
        ([("2024-05-01", "seed-history/a.md@1"), ("2024-02-01", "final")], "strictly increase"),
        ([("2024-02-01", "seed-history/a.md@1"), ("2024-02-01", "final")], "strictly increase"),
        ([("2024-02-01", "final"), ("2024-09-03", "seed-history/a.md@1")], "must be the last"),
        ([("2024-02-01", "seed-history/a.md@1"), ("2024-08-01", "final")], "seed-dates.tsv says"),
        ([("2024-02-01", "seed/elsewhere.md"), ("2024-09-03", "final")], "under seed-history/"),
    ],
)
def test_a_contradictory_history_is_refused(rows, fragment):
    history = [_rev("seed/a.md", d, PRIYA, s) for d, s in rows]
    with pytest.raises(replay.HistoryError, match=fragment.replace("`", ".")):
        replay.plan({"seed/a.md": "2024-09-03"}, history)


def test_a_document_the_rung_does_not_hold_is_refused():
    with pytest.raises(replay.HistoryError, match="does not hold"):
        replay.plan({"seed/a.md": "2024-09-03"}, [_rev("seed/z.md", "2024-09-03", PRIYA, "final")])


def test_a_revision_that_changes_nothing_is_refused():
    history = [
        _rev("seed/a.md", "2024-02-01", PRIYA, "seed-history/a.md@1"),
        _rev("seed/a.md", "2024-09-03", TOMASZ, "final"),
    ]
    with pytest.raises(replay.HistoryError, match="changes nothing"):
        replay.plan({"seed/a.md": "2024-09-03"}, history, read_source=lambda r: b"same")


def test_the_file_parser_refuses_a_bad_author_and_a_bad_date(tmp_path):
    f = tmp_path / "seed-history.tsv"
    f.write_text("seed/a.md\t2024-02-01\tPriya\tfinal\n", encoding="utf-8")
    with pytest.raises(replay.HistoryError, match="Name <email>"):
        replay.read_history(f)
    f.write_text(f"seed/a.md\t01/02/2024\t{PRIYA}\tfinal\n", encoding="utf-8")
    with pytest.raises(replay.HistoryError, match="YYYY-MM-DD"):
        replay.read_history(f)
    f.write_text(f"# comment\n\nseed/a.md\t2024-09-03\t{PRIYA}\tfinal\n", encoding="utf-8")
    assert replay.read_history(f) == [_rev("seed/a.md", "2024-09-03", PRIYA, "final")]


# -- the plan, replayed into a real repository -------------------------------


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not on PATH")
def test_a_replayed_plan_gives_git_the_authors_and_counts(tmp_path):
    """What step 8 will read, read the way it will read it — from `git log`."""
    golden = tmp_path / "golden"
    (golden / "seed-history").mkdir(parents=True)
    (golden / "seed-history" / "a.md@1").write_text("draft\n", encoding="utf-8")
    finals = {"seed/a.md": "final text\n", "seed/b.md": "b\n"}
    history = [
        _rev("seed/a.md", "2024-02-01", PRIYA, "seed-history/a.md@1"),
        _rev("seed/a.md", "2024-09-03", TOMASZ, "final"),
    ]
    dates = {"seed/a.md": "2024-09-03", "seed/b.md": "2024-01-15"}

    def source(rev):
        return finals[rev.path].encode() if rev.source == "final" else (golden / rev.source).read_bytes()

    repo = tmp_path / "rung"
    repo.mkdir()
    git = lambda *a, env=None: subprocess.run(  # noqa: E731
        ["git", *a], cwd=repo, check=True, capture_output=True, text=True, env=env
    ).stdout
    git("init", "-q", "-b", "main")
    git("config", "user.name", "fux-lab")
    git("config", "user.email", "lab@fux.example")
    import os

    for commit in replay.plan(dates, history, read_source=source):
        for rev in commit.revisions:
            (repo / rev.path).parent.mkdir(parents=True, exist_ok=True)
            (repo / rev.path).write_bytes(source(rev))
            git("add", "--", rev.path)
        stamp = f"{commit.date}T12:00:00+00:00"
        env = dict(os.environ, GIT_AUTHOR_NAME=commit.name, GIT_AUTHOR_EMAIL=commit.email,
                   GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp)
        git("commit", "-q", "-m", commit.message, env=env)

    log = git("log", "--format=%an|%as", "--", "seed/a.md").splitlines()
    assert log == ["Tomasz Kral|2024-09-03", "Priya Nair|2024-02-01"]
    assert (repo / "seed/a.md").read_text() == "final text\n"
    assert git("log", "-1", "--format=%as", "--", "seed/b.md").strip() == "2024-01-15"
