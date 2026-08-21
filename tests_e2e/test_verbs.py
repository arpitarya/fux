"""The M2 verb surface, exercised as a user through the real CLI.

The unit suite proves the differential law over synthetic corpora in-process.
This suite proves the *shipped commands* behave: that `ask` (the scan, by
default) and `ask --fast` (the accelerator) agree byte-for-byte on their
`--json` payloads, that `fux build` rebuilds a deleted derived plane, and that
the derived plane stays out of git.

Both suites are maintained; a feature is not done until both cover it
(CLAUDE.md §Build & test).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args], cwd=cwd, capture_output=True, text=True, check=check
    )


def _write_fixture(root: Path) -> None:
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = root / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs\n", encoding="utf-8")
    docs = root / "docs"
    docs.mkdir()
    (docs / "pruning.md").write_text(
        "---\ntitle: Why pruning failed\n---\n# Why pruning failed\n\n"
        "The gate measured static pruning twice and it did not preserve candidate recall.\n",
        encoding="utf-8",
    )
    (docs / "format.md").write_text(
        "---\ntitle: The committed index format\n---\n# The committed index format\n\n"
        "Doc-major canonical JSONL, sharded, sorted, with full postings.\n",
        encoding="utf-8",
    )
    (docs / "unrelated.md").write_text(
        "# Catering\n\nThe espresso beans arrive on Tuesdays.\n", encoding="utf-8"
    )


def test_ask_scans_by_default_and_fast_uses_the_accelerator(tmp_path):
    _write_fixture(tmp_path)
    out = _run(tmp_path, "ingest").stdout
    assert "accelerator:" in out
    assert (tmp_path / ".fux" / "runtime" / "stats.json").exists()

    by_default = _run(tmp_path, "ask", "why did pruning fail", "--explain").stdout
    assert "[scan]" in by_default

    fast = _run(tmp_path, "ask", "why did pruning fail", "--explain", "--fast").stdout
    assert "[accelerator]" in fast


def test_accelerator_and_scan_payloads_are_byte_identical(tmp_path):
    """The differential law, asserted through the shipped CLI.

    Not "the same documents" — the same bytes. This is the surface every
    downstream consumer and every future measurement actually reads.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    for query in ("why did pruning fail", "committed index format", "espresso", "nothing matches here"):
        for top in ("1", "5", "20"):
            scanned = _run(tmp_path, "ask", query, "--json", "--top", top).stdout
            accelerated = _run(tmp_path, "ask", query, "--json", "--top", top, "--fast").stdout
            assert accelerated == scanned, f"differential broken via CLI: {query!r} top={top}"


def test_build_rebuilds_a_deleted_derived_plane(tmp_path):
    """The derived plane is disposable by design — deleting it must be safe."""
    import shutil

    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    before = _run(tmp_path, "ask", "pruning", "--json", "--fast").stdout

    shutil.rmtree(tmp_path / ".fux" / "runtime")
    # With no accelerator, `ask` must still answer — from the reference scan,
    # which is the default now regardless.
    assert _run(tmp_path, "ask", "pruning", "--json").stdout == before

    assert "rebuilt" in _run(tmp_path, "build").stdout
    assert _run(tmp_path, "ask", "pruning", "--json", "--fast").stdout == before


def test_stale_accelerator_falls_back_rather_than_answering_wrongly(tmp_path):
    """A changed index must never be answered from a stale derived plane."""
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    (tmp_path / "docs" / "new.md").write_text("# Pruning again\n\npruning pruning pruning\n", encoding="utf-8")
    _run(tmp_path, "ingest", "--no-accelerator")

    # `--fast` is what actually reaches for the (now stale) accelerator; it
    # must fall back to the scan rather than answer from stale postings.
    explained = _run(tmp_path, "ask", "pruning", "--explain", "--fast").stdout
    assert "[scan]" in explained
    assert _run(tmp_path, "ask", "pruning", "--json").stdout == _run(
        tmp_path, "ask", "pruning", "--json", "--fast"
    ).stdout


def test_find_prints_locations_one_per_line(tmp_path):
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    lines = [l for l in _run(tmp_path, "find", "pruning", "--top", "2").stdout.splitlines() if l.strip()]
    assert lines
    assert all(l.endswith(".md") for l in lines)


def test_answer_fetches_and_re_scores_by_default(tmp_path):
    """PRIORITY.md P6: refer is the default path — a `file:` citation needs no
    fetcher (local checkout), so this never touches the network, but it does
    fetch fresh bytes, cite a fresh sha, and re-score a passage from them."""
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    payload = json.loads(_run(tmp_path, "answer", "why did pruning fail", "--json").stdout)
    assert payload["source"] == "refer"
    assert ".md" in payload["citation"]["loc"]  # a passage locator, e.g. "docs/pruning.md#p0"
    assert payload["citation"]["sha"]  # a fresh sha, not the indexed one's absence
    assert payload["citation"]["freshness"] == "current"
    assert payload["answer"]["passages"]
    assert payload["answer"]["passages"][0]["text"]

    human = _run(tmp_path, "answer", "why did pruning fail").stdout
    assert "sha " in human and "current" in human


def test_answer_sha_changes_when_the_source_file_changes(tmp_path):
    """PRIORITY.md P6's literal done-when: a passage + a sha that changes when
    the source changes — proving refer re-fetches rather than echoing the
    committed record's own (unchanged-until-ingest) sha."""
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    before = json.loads(_run(tmp_path, "answer", "why did pruning fail", "--json").stdout)

    (tmp_path / "docs" / "pruning.md").write_text(
        "---\ntitle: Why pruning failed\n---\n# Why pruning failed\n\n"
        "The gate measured static pruning twice and it did not preserve candidate recall. "
        "A third run confirmed the same failure.\n",
        encoding="utf-8",
    )
    # Deliberately NOT re-ingested — refer fetches the working tree directly,
    # so this must see the edit before the next `fux ingest` ever would.
    after = json.loads(_run(tmp_path, "answer", "why did pruning fail", "--json").stdout)

    assert after["source"] == "refer"
    assert after["citation"]["sha"] != before["citation"]["sha"]
    assert any("third run" in p["text"] for p in after["answer"]["passages"])


def test_answer_no_refer_keeps_the_index_only_path(tmp_path):
    """`--no-refer` must not imply refer ever ran — M2's bounded honesty line
    stays available on request."""
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    human = _run(tmp_path, "answer", "why did pruning fail", "--no-refer").stdout
    assert "--no-refer was passed" in human

    payload = json.loads(
        _run(tmp_path, "answer", "why did pruning fail", "--json", "--no-refer").stdout
    )
    assert payload["source"] == "index"
    assert payload["citation"]["loc"].endswith(".md")
    assert "sha" not in payload["citation"]  # the M2 shape, unchanged


def test_answer_declines_when_nothing_matches(tmp_path):
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    payload = json.loads(_run(tmp_path, "answer", "zzzz nothing", "--json").stdout)
    assert payload["answer"] is None


def test_answer_json_carries_source_on_both_branches(tmp_path):
    """W-48: ADR-ANSWER tells callers to key on `"source"` to detect the M4
    upgrade, so a branch that omits it is a trap rather than a signal. A hit
    now answers via refer; a miss has nothing to refer to and stays index.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    hit = json.loads(_run(tmp_path, "answer", "why did pruning fail", "--json").stdout)
    miss = json.loads(_run(tmp_path, "answer", "zzzz nothing", "--json").stdout)
    assert hit["source"] == "refer"
    assert miss["source"] == "index"
    assert miss["answer"] is None and miss["citation"] is None


def test_ask_json_reports_which_path_answered_when_explain_is_set(tmp_path):
    """W-48: `--explain` used to be text-only, so the one thing worth logging
    about a slow query was the one thing a caller could not read.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    plain = json.loads(_run(tmp_path, "ask", "pruning", "--json").stdout)
    assert "path" not in plain  # additive: silence unless asked

    explained = json.loads(_run(tmp_path, "ask", "pruning", "--json", "--explain").stdout)
    assert explained["path"] == "scan"  # the default
    assert explained["results"] == plain["results"]

    fast = json.loads(_run(tmp_path, "ask", "pruning", "--json", "--explain", "--fast").stdout)
    assert fast["path"] == "accelerator"


def test_find_still_prints_prose_on_the_no_match_path(tmp_path):
    """W-48 item 3, decided and left alone — pinned so the decision is visible.

    All three verbs say the same thing for the same condition; `--json` is the
    machine-readable form. ADR-FIND ties reopening this to a real script
    observed breaking on it, and no such script has been observed.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    result = _run(tmp_path, "find", "zzzz nothing")
    assert result.returncode == 0
    assert result.stdout.strip() == "No confident matches."
    assert result.stderr == ""


def test_derived_plane_is_gitignored(tmp_path):
    """ADR-DOTFUX's ignore rule, checked end to end rather than assumed."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, capture_output=True)
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "--", ".fux/runtime"], cwd=tmp_path, capture_output=True
    )
    assert ignored.returncode == 0, ".fux/runtime must be ignored — it is a derived plane"

    tracked = subprocess.run(
        ["git", "check-ignore", "-q", "--", ".fux/index"], cwd=tmp_path, capture_output=True
    )
    assert tracked.returncode == 1, ".fux/index is committed and must NOT be ignored"


def test_setup_writes_the_consumer_owned_files_and_never_rewrites_them(tmp_path):
    """`fux setup` as a user runs it — and the second run must change nothing."""
    (tmp_path / "docs").mkdir()
    first = _run(tmp_path, "setup")
    assert "wrote .fux/fetchers/http.py" in first.stdout
    assert (tmp_path / ".fux" / "fetchers" / "cdp.py").is_file()

    edited = tmp_path / ".fux" / "fetchers" / "http.py"
    edited.write_text("# my proxy lives here\n", encoding="utf-8")
    second = _run(tmp_path, "setup")
    assert "nothing to do" in second.stdout
    assert edited.read_text(encoding="utf-8") == "# my proxy lives here\n"


def test_machine_data_beside_a_document_is_not_indexed(tmp_path):
    """W-55 end to end: the walker has a type allowlist, and it is on by default.

    Before this, anything UTF-8-decodable was a document — 14% of this repo's
    own index was `.json`/`.svg`/`.sh`/`.py`, and a raw JSON blob ranked #2 on a
    plain query.
    """
    _write_fixture(tmp_path)
    (tmp_path / "docs" / "results.json").write_text(
        '{"pruning": "gate", "recall": 0.42}', encoding="utf-8"
    )
    (tmp_path / "docs" / "run.sh").write_text("#!/bin/sh\necho pruning\n", encoding="utf-8")

    out = _run(tmp_path, "ingest").stdout
    assert "not an indexed file type" in out

    found = _run(tmp_path, "find", "pruning", "--json").stdout
    assert "results.json" not in found and "run.sh" not in found


def test_a_types_file_replaces_the_default(tmp_path):
    _write_fixture(tmp_path)
    (tmp_path / "docs" / "note.rst").write_text("Pruning notes\n=============\n", encoding="utf-8")
    (tmp_path / ".fux" / "sources" / "types").write_text("*.rst\n", encoding="utf-8")

    _run(tmp_path, "ingest")
    found = _run(tmp_path, "find", "pruning", "--json").stdout
    assert "note.rst" in found
    assert "pruning.md" not in found  # the default no longer applies


def test_an_exclusion_line_removes_a_tree_from_the_walk(tmp_path):
    """W-45 end to end: committed evidence stops contaminating its own corpus."""
    _write_fixture(tmp_path)
    evidence = tmp_path / "docs" / "runs" / "r1" / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "dump.md").write_text(
        "# Why pruning failed\n\nraw output: why did pruning fail\n", encoding="utf-8"
    )
    (tmp_path / ".fux" / "sources" / "dirs").write_text(
        "docs\n!docs/runs/*/evidence\n", encoding="utf-8"
    )

    out = _run(tmp_path, "ingest").stdout
    assert "excluded by !docs/runs/*/evidence" in out
    assert "dump.md" not in _run(tmp_path, "find", "pruning", "--json").stdout


def test_setup_writes_the_types_file_with_the_default_spelled_out(tmp_path):
    """A consumer should not have to read fux's source to learn what a document is."""
    (tmp_path / "docs").mkdir()
    _run(tmp_path, "setup")
    types = (tmp_path / ".fux" / "sources" / "types").read_text(encoding="utf-8")
    assert "*.md" in types and "*.adoc" in types
    assert "No .json" in types  # it says what it excludes, and why


def test_ingest_puts_no_fetcher_in_a_repo_that_only_wanted_an_index(tmp_path):
    """ensure_layout writes the layout; only `fux setup` writes code."""
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    assert not (tmp_path / ".fux" / "fetchers").exists()


def test_add_records_a_url_line_and_no_fetch_keeps_it_offline(tmp_path):
    """Successor to the `fux url` surface test, which W-63 retired.

    `fux url` recorded and never fetched. `fux add <URL>` records **and**
    fetches that one URL — so the offline half of the old assertion now needs
    `--no-fetch`, which is exactly the flag that exists to ask for it.
    """
    _write_fixture(tmp_path)
    added = _run(
        tmp_path, "add", "https://example.invalid/handbook#oncall", "--cdp", "--no-fetch"
    )
    assert "fetch=cdp meta=hashed" in added.stdout
    assert "fetching" not in added.stderr  # --no-fetch means no network, and says nothing

    listed = _run(tmp_path, "add")
    assert "https://example.invalid/handbook#oncall fetch=cdp meta=hashed" in listed.stdout

    # The line is recorded; with no fetch there is nothing to index yet.
    found = _run(tmp_path, "find", "handbook", "--json")
    assert "example.invalid" not in found.stdout


def test_url_is_gone(tmp_path):
    """Deleted outright, not deprecated: four days old and pre-1.0 (W-63)."""
    _write_fixture(tmp_path)
    gone = _run(tmp_path, "url", "https://example.invalid/x", check=False)
    assert gone.returncode == 2  # argparse: not a choice


def test_refresh_urls_survives_one_release_as_a_hidden_alias(tmp_path):
    """The opposite call to `fux url`, and for a stated reason.

    It is a flag rather than a verb, it is older, and it is likelier to be in
    somebody's CI — so it keeps working, hidden from `--help`, for one
    release. `fux update` is what it now means.
    """
    _write_fixture(tmp_path)
    assert "--refresh-urls" not in _run(tmp_path, "ingest", "--help").stdout
    # No [sources.url] configured, so it fails the same way it always did —
    # what is asserted is that argparse still accepts the flag at all.
    still_parses = _run(tmp_path, "ingest", "--refresh-urls", check=False)
    assert still_parses.returncode != 2


# -- W-63: the source verbs, as a user --------------------------------------


def _shards(root: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted((root / ".fux" / "index").glob("*.jsonl"))}


def test_add_ingests_by_default(tmp_path):
    """`add` does the work — the whole reason it is not `git remote add`."""
    _write_fixture(tmp_path)
    (tmp_path / "handbook").mkdir()
    (tmp_path / "handbook" / "oncall.md").write_text(
        "---\ntitle: The oncall rota\n---\n# The oncall rota\n\nwho carries the pager\n",
        encoding="utf-8",
    )

    out = _run(tmp_path, "add", "handbook").stdout
    assert "added     handbook archived=false" in out
    assert "ingested" in out  # not a record-only verb

    assert "handbook/oncall.md" in _run(tmp_path, "find", "oncall rota").stdout


def test_add_then_ingest_produces_the_same_bytes(tmp_path):
    """The L3 assertion that matters most here.

    `add` must not be a second write path into the index. If it were, the
    bytes it produced and the bytes a plain `fux ingest` produces from the
    same list would differ — and nothing else in the suite would notice,
    because both would be internally consistent.
    """
    _write_fixture(tmp_path)
    (tmp_path / "handbook").mkdir()
    (tmp_path / "handbook" / "oncall.md").write_text("# Oncall\n\nthe pager\n", encoding="utf-8")

    _run(tmp_path, "add", "handbook")
    after_add = _shards(tmp_path)

    _run(tmp_path, "ingest")
    assert _shards(tmp_path) == after_add

    _run(tmp_path, "ingest", "--full")
    assert _shards(tmp_path) == after_add  # and a full run agrees with both


def test_remove_takes_the_document_out_of_the_index_and_the_graph(tmp_path):
    """The definition of done, asserted through the shipped verbs."""
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    assert "pruning.md" in _run(tmp_path, "find", "pruning").stdout

    out = _run(tmp_path, "remove", "docs/pruning.md").stdout
    assert "excluded  !docs/pruning.md" in out  # covered by `docs`, so an exclusion
    assert "dropped file:docs/pruning.md from the index" in out

    assert "pruning.md" not in _run(tmp_path, "find", "pruning").stdout
    assert "No confident matches." in _run(tmp_path, "ask", "why did pruning fail").stdout

    gone = _run(tmp_path, "explain", "docs/pruning.md", check=False)
    assert gone.returncode != 0


def test_remove_of_a_listed_entry_deletes_the_line(tmp_path):
    """The other branch of remove-by-coverage, through the CLI."""
    _write_fixture(tmp_path)
    (tmp_path / "handbook").mkdir()
    (tmp_path / "handbook" / "oncall.md").write_text("# Oncall\n\nthe pager\n", encoding="utf-8")
    _run(tmp_path, "add", "handbook")

    out = _run(tmp_path, "remove", "handbook").stdout
    assert "removed   handbook archived=false" in out
    assert "handbook" not in (tmp_path / ".fux" / "sources" / "dirs").read_text(encoding="utf-8")
    assert "dropped file:handbook/oncall.md from the index" in out


def test_the_differential_law_survives_an_add_and_a_remove(tmp_path):
    """Neither verb may move a ranking — they change the corpus, not the scorer."""
    _write_fixture(tmp_path)
    (tmp_path / "handbook").mkdir()
    (tmp_path / "handbook" / "oncall.md").write_text("# Oncall\n\nthe pager rota\n", encoding="utf-8")

    for step in (("add", "handbook"), ("remove", "docs/unrelated.md")):
        _run(tmp_path, *step)
        for query in ("pruning", "committed index format", "pager"):
            scanned = _run(tmp_path, "ask", query, "--json", "--top", "5").stdout
            accelerated = _run(tmp_path, "ask", query, "--json", "--top", "5", "--fast").stdout
            assert scanned == accelerated, f"differential broken after {step}: {query!r}"


def test_update_reingests_and_check_is_read_only(tmp_path):
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    (tmp_path / "docs" / "pruning.md").write_text(
        "---\ntitle: Why pruning failed\n---\n# Why pruning failed\n\n"
        "The gate measured static pruning twice. A third run confirmed it.\n",
        encoding="utf-8",
    )

    before = _shards(tmp_path)
    check = _run(tmp_path, "update", "--check")
    assert "stale" in check.stdout and "docs/pruning.md" in check.stdout
    assert _shards(tmp_path) == before  # --check wrote nothing

    _run(tmp_path, "update")
    assert _shards(tmp_path) != before
    assert "nothing has drifted" in _run(tmp_path, "update", "--check").stdout


def test_update_refuses_to_create_a_line(tmp_path):
    """`add` and `remove` write lines; `update` never touches one."""
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    refused = _run(tmp_path, "update", "docs/does-not-exist.md", check=False)
    assert refused.returncode == 1
    assert "never creates a line" in refused.stderr


def test_add_of_a_file_does_not_override_the_type_allowlist(tmp_path):
    """Inclusion is a conjunction with no precedence (ADR-DIR-LIST/ADR-TYPES).

    Promoting an explicitly-added file past the allowlist would be the W-55
    defect arriving from a new direction, so the line is written, the type
    check still runs, and the skip is reported with its reason.
    """
    _write_fixture(tmp_path)
    (tmp_path / "docs" / "architecture.pdf").write_bytes(b"%PDF-1.4 not really a pdf\n")

    out = _run(tmp_path, "add", "docs/architecture.pdf").stdout
    assert "added     docs/architecture.pdf archived=false" in out
    assert "skip docs/architecture.pdf: not an indexed file type" in out
    assert "architecture" not in _run(tmp_path, "find", "architecture").stdout


def test_dry_run_writes_no_bytes_anywhere(tmp_path):
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    dirs = tmp_path / ".fux" / "sources" / "dirs"
    before_list, before_shards = dirs.read_bytes(), _shards(tmp_path)

    _run(tmp_path, "add", "docs/format.md", "--dry-run")
    _run(tmp_path, "remove", "docs/format.md", "--dry-run")

    assert dirs.read_bytes() == before_list
    assert _shards(tmp_path) == before_shards
