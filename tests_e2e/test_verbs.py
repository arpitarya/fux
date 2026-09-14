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
        [sys.executable, "-m", "fux.cli", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=check
    )


def _write_fixture(root: Path) -> None:
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = root / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs\n", encoding="utf-8")
    # SR-PII decision 17: a repo without .fux/pii.toml refuses; empty redacts nothing.
    (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
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


def test_retirement_marks_and_never_demotes(tmp_path):
    """SR-ARCHIVED-CONTENT decisions 2, 3 and 6, through the shipped CLI.

    🔴 **REVERSED 2026-09-13.** `archived_weight` let a consumer demote retired
    documents and was removed (SR-TUNE decision 15a, W-152): retirement is a
    fact, and fux does not scale a score by a fact. So this asserts three things
    that are now structural rather than default-dependent — the archived
    document still wins on its text, it is still **marked**, and a committed
    `archived_weight` is **refused by name** rather than read.
    """
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = tmp_path / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs\nold archived=true\n", encoding="utf-8")
    # SR-PII decision 17: a repo without .fux/pii.toml refuses; empty redacts nothing.
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "cache.md").write_text(
        "---\ntitle: Old cache\n---\n# Old cache\n\ncache cache cache design\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "cache.md").write_text(
        "---\ntitle: New cache\n---\n# New\n\na passing mention of cache\n", encoding="utf-8"
    )
    _run(tmp_path, "ingest")

    default = json.loads(_run(tmp_path, "ask", "cache", "--json").stdout)["results"]
    assert default[0]["loc"] == "old/cache.md"  # heading match wins, undemoted
    assert default[0]["archived"] is True  # and the reader is TOLD

    # The removed key is an error that names the removal, not an unknown key.
    (tmp_path / ".fux" / "tune.toml").write_text(
        "[ranking]\narchived_weight = 0.1\n", encoding="utf-8"
    )
    refused = _run(tmp_path, "ask", "cache", "--json", check=False)
    assert refused.returncode == 1
    assert "REMOVED on 2026-09-13" in refused.stderr

    # `--no-tune` skips the file entirely (SR-TUNE decision 11), so it answers
    # even while a removed key sits in it — which is what that switch is for.
    untuned = _run(tmp_path, "ask", "cache", "--json", "--no-tune").stdout
    assert json.loads(untuned)["results"][0]["loc"] == "old/cache.md"


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


def test_find_precision_controls(tmp_path):
    """W-111, through the shipped CLI. Each flag REMOVES results the ranking
    already produced, and says on **stderr** how many — stdout stays a bare
    path list a pipe can read."""
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    plain = _run(tmp_path, "find", "pruning index format").stdout.split()
    assert len(plain) >= 2, "precondition: the query must reach more than one document"

    under = _run(tmp_path, "find", "pruning index format", "--under", "docs/pru")
    assert under.stdout.split() == ["docs/pruning.md"]
    assert "[filter] --under removed" in under.stderr

    # `--all` demands every query term; only one fixture document has both.
    every = _run(tmp_path, "find", "pruning recall", "--all")
    assert every.stdout.split() == ["docs/pruning.md"]

    # The phrase is in `pruning.md` verbatim and nowhere else.
    phrase = _run(tmp_path, "find", "static pruning candidate", "--phrase", "static pruning")
    assert phrase.stdout.split() == ["docs/pruning.md"]

    # Nothing on stdout but paths, under every filter.
    for out in (under.stdout, every.stdout, phrase.stdout):
        assert all(line.endswith(".md") for line in out.split())


def test_ask_marks_a_tie_and_json_always_carries_the_flag(tmp_path):
    """W-111. `tie` is `required: always`: `false` is a claim a caller needs,
    and an absent key is indistinguishable from an older fux."""
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    payload = json.loads(_run(tmp_path, "ask", "why did pruning fail", "--json").stdout)
    assert payload["results"], "precondition: the query must return something"
    for r in payload["results"]:
        assert isinstance(r["tie"], bool), "`tie` must be present on every row"

    human = _run(tmp_path, "ask", "why did pruning fail").stdout
    for line, r in zip([l for l in human.splitlines() if l and not l.startswith(" ")], payload["results"]):
        assert ("(tie)" in line) is r["tie"], "the text marker and the JSON flag must agree"


def test_answer_cites_across_documents_and_names_each_one(tmp_path):
    """W-108, through the shipped CLI.

    `answer` refers the top 3, so `answer.passages` can span documents — and
    every entry names its own `id`, `loc` and `sha`. **Before W-108 the text
    surface printed one trailing locator for the whole answer**, which named
    the first passage's line range whatever the second passage was; with three
    documents it would name the wrong file. Each passage now prints under its
    own locator.

    `citation` is unchanged: the winning passage's document, and the only key a
    caller that wants one answer needs to read.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    # A query whose terms are spread across two of the three fixture documents.
    payload = json.loads(
        _run(tmp_path, "answer", "pruning gate index format postings", "--json").stdout
    )
    assert payload["source"] == "refer"
    passages = payload["answer"]["passages"]
    assert len(passages) >= 2
    for p in passages:
        assert p["id"].startswith("file:")
        assert p["loc"].endswith(tuple(str(n) for n in range(10)))  # ends in a line number
        assert p["sha"]
    assert {p["id"] for p in passages} > {payload["citation"]["id"]}, (
        "the fixture query must reach more than one document, or this asserts nothing"
    )
    assert payload["citation"]["id"] == passages[0]["id"]

    human = _run(tmp_path, "answer", "pruning gate index format postings").stdout
    # One locator line per passage, not one for the answer.
    assert human.count("  -- ") == len(passages)
    for p in passages:
        assert f"  -- {p['loc']} (sha {p['sha'][:12]}" in human


def test_every_passage_carries_its_ordinal(tmp_path):
    """SR-REFER decision 17 and SR-ANSWER decision 9, through the CLI.

    **Both records promised `passage.ordinal` in the `--json` payload and the
    code did not emit it** (W-140 row 2). The reason it is promised is worth
    keeping: the locator is a LINE RANGE, and a reflow that moves every line
    number silently invalidates a stored citation — the ordinal is what
    survives that. A reader following the record would have found nothing.

    ⚠ **It is asserted through `subprocess`, not on the dataclass.** The claim
    the records make is about the payload a consumer parses; a unit test on
    `Citation` would pass while the emitter dropped the field, which is exactly
    how this went unnoticed.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    payload = json.loads(
        _run(tmp_path, "answer", "pruning gate index format postings", "--json").stdout
    )
    passages = payload["answer"]["passages"]
    assert passages, "the fixture query must return passages, or this asserts nothing"
    for p in passages:
        assert isinstance(p["ordinal"], int) and p["ordinal"] >= 0, p


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
    """W-48: SR-ANSWER tells callers to key on `"source"` to detect the M4
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


def test_every_json_hit_carries_mtime_through_the_shipped_cli(tmp_path):
    """W-153 — the committed date reaches a caller, on `ask` and on `find`.

    🔴 **This fixture is NOT a git repository**, deliberately: `mtime` comes from
    git commit times, so every document here has none. That is the exact shape a
    corpus copied out of its repository has, and the assertion is that the key is
    **present and `null`** rather than missing — an absent key cannot be told
    from an older fux (the W-48 trap).

    Both paths are checked, because the field is read in `rank()` off a record
    dict the scan and the accelerator both supply.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    for extra in ([], ["--fast"]):
        hits = json.loads(_run(tmp_path, "ask", "pruning", "--json", *extra).stdout)["results"]
        assert hits
        for hit in hits:
            assert "mtime" in hit, "an absent key is indistinguishable from an older fux"
            assert hit["mtime"] is None, "no git history here, so no committed date"

    found = json.loads(_run(tmp_path, "find", "pruning", "--json").stdout)["results"]
    assert found and all("mtime" in hit for hit in found)


# -- SR-PROVENANCE decision 10, as amended: the journal's TWO consent surfaces --


def _journal(root: Path) -> Path:
    from fux.query.provenance import JOURNAL_NAME

    return root / ".fux" / "runtime" / JOURNAL_NAME


def test_both_journal_consent_surfaces_write_and_neither_alone_is_removable(tmp_path):
    """🔴 W-147, ruled by Arpit 2026-09-13: *"I need the flag as well as output
    TOML configuration."* **Both are explicit consent and both stay.**

    This test exists so neither can be tidied away by a later session reading
    `.fux/output.toml` as a pure *rendering* config. It is not — `journal` is a
    **declared exception** to SR-OUTPUT decision 2's boundary rule: it leaves the
    result set byte-identical and still **writes a durable file**, which is
    exactly why the boundary rule alone was never going to catch it.

    Four cases, and the fourth is the one that makes the other three mean
    something: **neither surface present must write nothing at all.**
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    q = "pruning"

    # 1 · neither surface -> NO journal. The default is `false` on both.
    _run(tmp_path, "answer", q, "--json")
    assert not _journal(tmp_path).exists(), "a journal appeared with no consent of any kind"

    # 2 · the flag alone, no config -> journals.
    _run(tmp_path, "answer", q, "--json", "--journal")
    assert _journal(tmp_path).exists(), "`--journal` did not write"
    flag_lines = len(_journal(tmp_path).read_text(encoding="utf-8").splitlines())
    assert flag_lines >= 1

    # 3 · the committed key alone, NO flag -> journals. This is the half the
    #     ruling turns on: a repository-level opt-in, reviewable in git, is
    #     consent in a way that watching somebody's terminal is not.
    #
    # ⚠ The file is the SPECIMEN with one line flipped, not a two-line snippet.
    # `.fux/output.toml` is a COMPLETE declaration: once it exists every gated
    # key must be set, and a sparse file is refused by name. That is the shape a
    # consumer actually has — `fux setup` writes the specimen and they edit a
    # line — so testing the snippet would test a file nobody has.
    from fux.output_config import specimen

    _journal(tmp_path).unlink()
    body = specimen().replace("journal = false", "journal = true")
    assert "journal = true" in body, "the specimen's journal line changed spelling"
    (tmp_path / ".fux" / "output.toml").write_text(body, encoding="utf-8")
    _run(tmp_path, "answer", q, "--json")
    assert _journal(tmp_path).exists(), (
        "a committed `[cli.answer] journal = true` did not write — SR-PROVENANCE "
        "decision 10 as amended says it is consent, so this is the ruling broken"
    )

    # 4 · `--no-output-config` ignores the file, so the committed key stops
    #     applying. The escape hatch has to reach this key like any other.
    _journal(tmp_path).unlink()
    _run(tmp_path, "answer", q, "--json", "--no-output-config")
    assert not _journal(tmp_path).exists(), (
        "`--no-output-config` did not reach `journal`, so a consumer cannot turn "
        "a committed opt-in off for one invocation"
    )


def test_journal_is_refused_by_name_at_the_shared_cli_level(tmp_path):
    """It is PER-VERB, and that has not changed.

    `[cli] journal = true` would turn journalling on for verbs that have no such
    flag, which is a different and much larger consent than the one Arpit ruled.
    The refusal names the key rather than reporting an unknown one.
    """
    _write_fixture(tmp_path)
    (tmp_path / ".fux" / "output.toml").write_text(
        "[cli]\njournal = true\n", encoding="utf-8")
    out = _run(tmp_path, "answer", "pruning", "--json", check=False)
    assert out.returncode != 0
    assert "journal" in out.stderr, out.stderr


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


def test_the_no_match_prose_is_on_stderr_and_stdout_is_empty(tmp_path):
    """W-165 fix 2 — the golden updated BY HAND, in the change that moved it.

    **It asserted the opposite until 2026-09-14.** W-48 item 3 had left the
    sentence on stdout and SR-FIND tied reopening to *"a real script observed
    breaking on it"*. No script was ever observed, and the reopen came from the
    other direction: the surface is documented as needing a `grep -qx` guard
    before a caller may pipe `find`, which is a contract made of a string.

    **Empty stdout is the assertion that matters** — that is what makes an empty
    result read as zero paths rather than one that happens to be prose.

    The exit code stays 0 (SR-CLI decision 6: an honest decline is a successful
    run) and the wording is unchanged, so a consumer matching the text keeps
    matching it on the other stream.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    for verb in ("find", "ask", "answer"):
        result = _run(tmp_path, verb, "zzzz nothing")
        assert result.returncode == 0, verb
        assert result.stdout == "", verb
        assert result.stderr.strip() == "No confident matches.", verb


def test_the_no_match_json_never_carried_the_prose(tmp_path):
    """`--json` is unaffected by the stream move, because it never printed it.

    The companion to the test above: a JSON caller's contract is `results: []`
    and it is the same before and after W-165 fix 2, on both streams.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    result = _run(tmp_path, "find", "zzzz nothing", "--json")
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"results": []}
    assert "No confident matches." not in result.stderr


def test_derived_plane_is_gitignored(tmp_path):
    """SR-DOTFUX's ignore rule, checked end to end rather than assumed."""
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

    ⚠ **Rewritten 2026-08-27.** This test asserted that `.json` was not indexed,
    which stopped being true on **2026-08-26**, when Arpit ruled the default
    allowlist out to *"all the ones which have a decoder"*. The W-55 measurement
    was never overturned — what changed is that those tokens were RAW BYTES, and
    `.json` now passes through a decoder that keeps string values and drops ids,
    hashes, timestamps and numbers.

    **So the guard moved rather than went away.** `.sh` has no decoder and is
    still not a document; `.json` is one, and the machine noise inside it is
    still not searchable. Both halves are asserted, because either one silently
    reversing is the W-55 defect returning.
    """
    _write_fixture(tmp_path)
    (tmp_path / "docs" / "results.json").write_text(
        '{"pruning": "gate", "recall": 0.42, '
        '"run_id": "8f14e45f-ceea-467a-9b3d-9f0a3b2c1d4e", '
        '"stamp": "2026-08-26T10:00:00Z"}',
        encoding="utf-8",
    )
    (tmp_path / "docs" / "run.sh").write_text("#!/bin/sh\necho pruning\n", encoding="utf-8")

    out = _run(tmp_path, "ingest").stdout
    assert "not an indexed file type" in out, "the allowlist still bites, and says so"

    # A format with no decoder is still not a document, however decodable its
    # bytes happen to be as UTF-8.
    found = _run(tmp_path, "find", "pruning", "--json").stdout
    assert "run.sh" not in found

    # ...and one with a decoder IS. Asserted positively so a silent narrowing of
    # the default is a failure here rather than a quietly smaller index.
    assert "results.json" in found

    # The half that makes that safe: nothing a machine wrote is a search term.
    for noise in ("8f14e45f-ceea-467a-9b3d-9f0a3b2c1d4e", "2026-08-26T10:00:00Z", "0.42"):
        assert "results.json" not in _run(tmp_path, "find", noise, "--json").stdout, (
            f"{noise!r} reached the index — the decoder stopped dropping machine "
            "values, which is what re-admitting .json was conditional on"
        )


def test_a_types_file_replaces_the_default(tmp_path):
    _write_fixture(tmp_path)
    (tmp_path / "docs" / "note.rst").write_text("Pruning notes\n=============\n", encoding="utf-8")
    (tmp_path / ".fux" / "formats.toml").write_text('include = ["*.rst"]\n', encoding="utf-8")

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
    types = (tmp_path / ".fux" / "formats.toml").read_text(encoding="utf-8")
    assert '"*.md"' in types and '"*.adoc"' in types

    # ⚠ Was `assert "No .json" in types`. `.json` rejoined the default on
    # 2026-08-26 (Arpit: *"all the ones which have a decoder"*), so that line
    # was asserting a sentence the template no longer has a reason to write.
    # Since SR-TYPES decision 12 a decoded format is a `[decoders]` line.
    assert '\njson = "json"\n' in types, "a decoded format is spelled out like any other"

    # The claim the test was really making — that the file says what is OUT and
    # why — restated against what it now says.
    assert "What is OUT of the default, and why" in types

    # ⚠ Was `assert "\n#*.svg" in types`. `.svg` rejoined the default on
    # 2026-08-29 when `svg` shipped as a built-in, which left the template
    # asserting a line that CONTRADICTED the file it was in: `*.svg` was an
    # active line above and a commented "not indexed until you uncomment"
    # line below, under a heading reading "nothing here has a built-in
    # decoder". The stale half was dropped on 2026-09-01. `#*.log` is the
    # genuine article — no built-in reads it — and carries the same claim.
    assert '\n# log = "<your module>"' in types, "an opt-in format is present but commented"
    assert "\n# svg =" not in types, "a format with a built-in decoder is not an opt-in"
    assert '\nsvg = "svg"\n' in types, "…it is an active line, bound to its decoder"
    assert '"*.sh"' not in types and "\nsh =" not in types, "no decoder, not an active line"


def test_setup_converts_a_leftover_types_file_and_ingest_refuses_until_it_is_gone(tmp_path):
    """SR-TYPES decision 12, end to end: refused, converted, then deleted by hand."""
    _write_fixture(tmp_path)
    (tmp_path / "docs" / "note.rst").write_text("Pruning notes\n=============\n", encoding="utf-8")
    legacy = tmp_path / ".fux" / "sources" / "types"
    legacy.write_text("*.rst\n", encoding="utf-8")

    refused = subprocess.run([sys.executable, "-m", "fux.cli", "ingest"], cwd=tmp_path,
                             capture_output=True, text=True, encoding="utf-8")
    assert refused.returncode == 1 and "fux setup" in refused.stderr

    out = _run(tmp_path, "setup").stdout
    assert (tmp_path / ".fux" / "formats.toml").is_file()
    assert "now delete .fux/sources/types" in out and legacy.is_file()
    legacy.unlink()
    _run(tmp_path, "ingest")
    found = _run(tmp_path, "find", "pruning", "--json").stdout
    assert "note.rst" in found and "pruning.md" not in found, "the conversion kept the allowlist"


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
    # W-165 fix 1: the exclusion is a `.fuxignore` line now, anchored with a
    # leading `/` so it cannot also drop an `archive/docs/pruning.md`.
    assert "excluded  /docs/pruning.md" in out  # covered by `docs`, so an exclusion
    assert "dropped file:docs/pruning.md from the index" in out

    assert "pruning.md" not in _run(tmp_path, "find", "pruning").stdout
    assert "No confident matches." in _run(tmp_path, "ask", "why did pruning fail").stderr

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
    """Inclusion is a conjunction with no precedence (SR-DIR-LIST/SR-TYPES).

    Promoting an explicitly-added file past the allowlist would be the W-55
    defect arriving from a new direction, so the line is written, the type
    check still runs, and the skip is reported with its reason.

    ⚠ **The fixture was `architecture.pdf` until 2026-08-27**, which stopped
    testing this the day `.pdf` joined the default allowlist — the file was
    admitted by type and then failed to *decode*, which is a different check
    with a different outcome. `.sh` has no decoder and is not in the default,
    so it is what this assertion has always meant.
    """
    _write_fixture(tmp_path)
    (tmp_path / "docs" / "deploy.sh").write_text("#!/bin/sh\necho architecture\n", encoding="utf-8")

    out = _run(tmp_path, "add", "docs/deploy.sh").stdout
    assert "added     docs/deploy.sh archived=false" in out
    assert "not indexed docs/deploy.sh: not an indexed file type" in out
    assert "architecture" not in _run(tmp_path, "find", "architecture").stdout


def test_an_added_file_that_no_decoder_can_read_is_queued_not_fatal(tmp_path):
    """The check the old fixture was accidentally exercising, made deliberate.

    An allowed TYPE that nothing can DECODE is a third outcome, distinct from
    both "indexed" and "wrong type": the run completes, the document gets no
    record, and it is written to the committed queue as work a model is owed.

    ⚠ **This crashed until 2026-08-27** — `run()`'s record loop iterated every
    walked file and reached `file_shas[doc_id]` for one the parse plane had
    dropped, so a single undecodable `%PDF` header ended the entire ingest with
    a `KeyError`. Gated in the unit suite too
    (`tests/ingest/test_unreadable_document.py`); kept here because the crash
    was only ever visible through the shipped command.
    """
    _write_fixture(tmp_path)
    (tmp_path / "docs" / "architecture.pdf").write_bytes(b"%PDF-1.4 not really a pdf\n")

    added = _run(tmp_path, "add", "docs/architecture.pdf")
    assert added.returncode == 0, added.stderr
    assert "added     docs/architecture.pdf archived=false" in added.stdout

    # No record: a document with no extraction behind it would rank on its
    # filename alone, which is W-55 arriving through the decoder plane.
    assert "architecture" not in _run(tmp_path, "find", "architecture").stdout

    # Dropped, not forgotten.
    queue = list((tmp_path / ".fux").rglob("*queue*"))
    assert queue, "the unreadable document was not written down anywhere"
    assert "docs/architecture.pdf" in queue[0].read_text(encoding="utf-8")


def test_dry_run_writes_no_bytes_anywhere(tmp_path):
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    dirs = tmp_path / ".fux" / "sources" / "dirs"
    before_list, before_shards = dirs.read_bytes(), _shards(tmp_path)

    _run(tmp_path, "add", "docs/format.md", "--dry-run")
    _run(tmp_path, "remove", "docs/format.md", "--dry-run")

    assert dirs.read_bytes() == before_list
    assert _shards(tmp_path) == before_shards


# -- W-174: `fetch_at_answer = false`, through the real CLI -------------------

#: Logs every lifecycle call. **The absence of this file after `answer` is the
#: assertion** — stronger than reading a mode out of the JSON, because it
#: proves no consumer code ran at all, not merely that no fetch was attempted.
_LOGGING_FETCHER = '''\
import pathlib

LOG = pathlib.Path(__file__).with_name("calls.log")

def _log(line):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\\n")

def connect():
    _log("connect")

def close():
    _log("close")

def fetch(url):
    _log("fetch:" + url)
    return "# Runbook\\n\\nRestart the indexer with `fux build --force`.\\n"
'''


def _url_repo(tmp_path: Path, *, extra: str = "") -> None:
    (tmp_path / "fux.toml").write_text(
        "[sources]\n"
        "[sources.url]\n"
        'fetcher = "mw.py"\n'
        "max_parallel = 4\n" + extra,
        encoding="utf-8",
    )
    (tmp_path / "mw.py").write_text(_LOGGING_FETCHER, encoding="utf-8")
    fux = tmp_path / ".fux"
    (fux / "sources").mkdir(parents=True, exist_ok=True)
    (fux / "sources" / "dirs").write_text("", encoding="utf-8")
    (fux / "sources" / "urls").write_text("https://x.test/runbook\n", encoding="utf-8")
    (fux / "pii.toml").write_text("", encoding="utf-8")


def test_fetch_at_answer_false_answers_from_acquired_and_opens_no_socket(tmp_path):
    """The whole feature, as a user sees it.

    Ingest retains the bytes (`keep` defaults to true), then the flag goes on
    and `answer` must produce a real, verified citation without the fetcher
    being loaded, configured, connected or called.
    """
    _url_repo(tmp_path)
    # ⚠ `--refresh-urls`: a plain `ingest` never opens a socket (SR-MAINTENANCE
    # decision 5a), so without it the URL is listed and not in the index, and
    # this test would pass for the wrong reason.
    _run(tmp_path, "ingest", "--refresh-urls")
    assert (tmp_path / ".fux" / "acquired" / "manifest.json").exists()

    # Everything up to here was allowed to fetch; only what follows is on trial.
    (tmp_path / "calls.log").unlink()
    _url_repo(tmp_path, extra="fetch_at_answer = false\n")

    out = _run(tmp_path, "answer", "how do I restart the indexer", "--json").stdout
    payload = json.loads(out)

    assert payload["source"] == "refer"
    assert payload["citation"]["freshness"] == "as-ingested"
    assert not (tmp_path / "calls.log").exists(), "the fetcher was touched under `never`"


def test_the_default_still_fetches_so_no_repo_changes_meaning(tmp_path):
    """The other half of the same claim: silence is today's behaviour."""
    _url_repo(tmp_path)
    _run(tmp_path, "ingest", "--refresh-urls")
    (tmp_path / "calls.log").unlink()

    _run(tmp_path, "answer", "how do I restart the indexer", "--json")
    log = (tmp_path / "calls.log").read_text(encoding="utf-8")
    assert "fetch:https://x.test/runbook" in log


def test_a_misspelled_flag_is_refused_rather_than_silently_ignored(tmp_path):
    """The failure this key would otherwise have: a consumer who believes they
    are offline, and is not."""
    _url_repo(tmp_path, extra="fetch_at_anwser = false\n")
    done = _run(tmp_path, "doctor", check=False)
    assert done.returncode != 0
    assert "not a fux.toml key" in (done.stdout + done.stderr)
