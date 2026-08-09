"""Profiles (full/lean/auto), the LRU, and `db pull`.

The headline is :func:`test_switching_to_lean_mid_corpus_keeps_rankings` —
Arpit's M7 requirement: ingest full, switch the profile, and every ranking must
be identical, because both profiles feed the scorer the same numbers.
"""

from __future__ import annotations

import json

import pytest

from fux.config import load
from fux.errors import FuxError
from fux.index import leancache
from fux.ingest import dbpull
from fux.query.profile import resolve

from test_df_sidecar import rich_project
from test_ingest import run


def set_profile(tmp_path, profile: str, extra: str = "") -> None:
    base = (tmp_path / "fux.toml").read_text(encoding="utf-8").split("[index]")[0]
    (tmp_path / "fux.toml").write_text(
        f'{base}\n[index]\nprofile = "{profile}"\n{extra}', encoding="utf-8"
    )


def query(tmp_path, monkeypatch, capsys, *args):
    capsys.readouterr()
    run(tmp_path, monkeypatch, *args)
    return json.loads(capsys.readouterr().out)


# -- resolution ------------------------------------------------------------


def test_explicit_profiles_are_honoured(tmp_path, monkeypatch):
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    set_profile(tmp_path, "lean")
    assert resolve(load(tmp_path)) == "lean"
    set_profile(tmp_path, "full")
    assert resolve(load(tmp_path)) == "full"


def test_auto_stays_full_below_the_size_threshold(tmp_path, monkeypatch):
    """Lean buys footprint at the cost of cold derives; small corpora gain nothing."""
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    set_profile(tmp_path, "auto")
    assert resolve(load(tmp_path)) == "full"


def test_auto_picks_lean_once_the_corpus_is_large(tmp_path, monkeypatch):
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    set_profile(tmp_path, "auto", "lean_threshold = 1\n")
    assert resolve(load(tmp_path)) == "lean"


def test_auto_refuses_lean_for_a_mirror_tier(tmp_path, monkeypatch):
    """Mirror text came from the network; re-deriving it would mean re-crawling."""
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    (tmp_path / "fux.toml").write_text(
        (tmp_path / "fux.toml").read_text(encoding="utf-8")
        + '\n[index]\nprofile = "auto"\nlean_threshold = 1\n'
        + '\n[sources.web]\nurls = ["https://x.test/"]\ntier = "mirror"\n',
        encoding="utf-8",
    )
    assert resolve(load(tmp_path)) == "full"


def test_auto_refuses_lean_when_a_source_is_missing(tmp_path, monkeypatch):
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    set_profile(tmp_path, "auto", "lean_threshold = 1\n")
    (tmp_path / "docs" / "rollback.md").unlink()
    assert resolve(load(tmp_path)) == "full"


# -- the parity requirement ------------------------------------------------


QUERIES = (
    "how fast are rollbacks after failed health checks",
    "telemetry exporter batches",
    "install the widget service",
    "rollback",
)


def test_switching_to_lean_mid_corpus_keeps_rankings(tmp_path, monkeypatch, capsys):
    """Ingest full → switch to lean → identical rankings and scores (M7)."""
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")

    full = {q: query(tmp_path, monkeypatch, capsys, "find", q, "--json") for q in QUERIES}
    set_profile(tmp_path, "lean")
    leancache.clear(tmp_path)
    for q in QUERIES:
        lean = query(tmp_path, monkeypatch, capsys, "find", q, "--json")
        assert [r["path"] for r in lean["results"]] == [
            r["path"] for r in full[q]["results"]
        ], f"ranking diverged for {q!r}"
        for a, b in zip(lean["results"], full[q]["results"]):
            assert a["score"] == pytest.approx(b["score"], rel=1e-9), f"score: {q!r}"
    # Guard against a vacuous pass: if lean_searcher had quietly returned None
    # the full path would have answered and this test would prove nothing.
    assert leancache.stats(tmp_path)[0] > 0, "the lean path never actually ran"


def test_lean_ask_matches_full_ask(tmp_path, monkeypatch, capsys):
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    full = query(tmp_path, monkeypatch, capsys, "ask", QUERIES[0], "--json")
    set_profile(tmp_path, "lean")
    lean = query(tmp_path, monkeypatch, capsys, "ask", QUERIES[0], "--json")
    assert [(r["path"], r["line_start"]) for r in lean["results"]] == [
        (r["path"], r["line_start"]) for r in full["results"]
    ]


def test_lean_reports_the_true_corpus_size(tmp_path, monkeypatch, capsys):
    """Lean scores a candidate slice but must never report the slice as the corpus."""
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    full = query(tmp_path, monkeypatch, capsys, "find", "rollback", "--json")
    set_profile(tmp_path, "lean")
    lean = query(tmp_path, monkeypatch, capsys, "find", "rollback", "--json")
    assert lean["corpus"] == full["corpus"]


def test_lean_lexical_only_matches_full(tmp_path, monkeypatch, capsys):
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    full = query(tmp_path, monkeypatch, capsys, "find", "rollback", "--json", "--lexical-only")
    set_profile(tmp_path, "lean")
    lean = query(tmp_path, monkeypatch, capsys, "find", "rollback", "--json", "--lexical-only")
    assert lean["results"] == full["results"]


# -- the LRU ---------------------------------------------------------------


def test_cache_round_trips(tmp_path):
    chunks = [{"heading": "H", "text": "body", "start": 1, "end": 2, "words": 1}]
    leancache.put(tmp_path, "docs/a.md", "abc123", chunks, 200)
    assert leancache.get(tmp_path, "docs/a.md", "abc123") == chunks


def test_a_changed_sha_is_a_miss_not_stale_content(tmp_path):
    leancache.put(tmp_path, "docs/a.md", "old", [{"heading": "H", "text": "x"}], 200)
    assert leancache.get(tmp_path, "docs/a.md", "new") is None


def test_eviction_drops_least_recently_touched_first(tmp_path):
    big = [{"heading": "H", "text": "x" * 4000}]
    for name in ("a", "b", "c"):
        leancache.put(tmp_path, f"docs/{name}.md", "s", big, 200)
    leancache.get(tmp_path, "docs/a.md", "s")  # touch a, so b is now oldest
    leancache.put(tmp_path, "docs/d.md", "s", big, 0)  # budget 0 forces eviction
    entries, _ = leancache.stats(tmp_path)
    assert entries < 4
    assert leancache.get(tmp_path, "docs/b.md", "s") is None


def test_cache_is_bounded_by_the_budget(tmp_path):
    payload = [{"heading": "H", "text": "y" * 20_000}]
    for i in range(20):
        leancache.put(tmp_path, f"docs/{i}.md", "s", payload, 0)
    _, total = leancache.stats(tmp_path)
    assert total <= 20_000 * 2  # bounded, not unbounded growth


def test_cache_never_changes_a_result(tmp_path, monkeypatch, capsys):
    """Cold and warm queries must agree — the cache is speed, not semantics."""
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    set_profile(tmp_path, "lean")
    leancache.clear(tmp_path)
    cold = query(tmp_path, monkeypatch, capsys, "find", "rollback", "--json")
    warm = query(tmp_path, monkeypatch, capsys, "find", "rollback", "--json")
    assert cold == warm
    assert leancache.stats(tmp_path)[0] > 0, "the second query should have been warm"


# -- db pull ---------------------------------------------------------------


def test_install_verifies_the_sha(tmp_path, monkeypatch):
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    config = load(tmp_path)
    from fux.ingest.manifest import sha256_bytes

    data = b"a pretend database"
    dbpull.install(config, data, expected=sha256_bytes(data))
    assert (tmp_path / ".fux/index/fux.db").read_bytes() == data


def test_install_refuses_a_mismatch_and_writes_nothing(tmp_path, monkeypatch):
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    config = load(tmp_path)
    before = (tmp_path / ".fux/index/fux.db").read_bytes() if (
        tmp_path / ".fux/index/fux.db"
    ).is_file() else None

    with pytest.raises(FuxError, match="sha256 mismatch"):
        dbpull.install(config, b"wrong artifact", expected="0" * 64)

    after = (tmp_path / ".fux/index/fux.db").read_bytes() if (
        tmp_path / ".fux/index/fux.db"
    ).is_file() else None
    assert after == before, "a refused pull must not touch the existing index"


def test_expected_sha_reads_the_lock(tmp_path, monkeypatch):
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    from fux.ingest.lock import read as lock_read, write as lock_write

    assert dbpull.expected_sha(load(tmp_path)) is None  # nothing published yet
    records = list(lock_read(tmp_path).values())
    records.append({"id": dbpull.LOCK_DB_KEY, "kind": "artifact", "sha256": "f" * 64})
    lock_write(tmp_path, records)
    assert dbpull.expected_sha(load(tmp_path)) == "f" * 64


def test_non_http_urls_are_refused():
    with pytest.raises(FuxError, match="http"):
        dbpull.fetch("file:///etc/passwd")


def test_auth_header_comes_from_the_environment(tmp_path, monkeypatch):
    """Credentials via env var, never a flag — flags land in shell history."""
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["auth"] = request.get_header("Authorization")
        raise FuxError("stop here")  # we only care about the header

    monkeypatch.setenv(dbpull.AUTH_ENV, "Bearer secret-token")
    monkeypatch.setattr("fux.ingest.dbpull.urlopen", fake_urlopen)
    with pytest.raises(FuxError):
        dbpull.fetch("https://x.test/fux.db")
    assert captured["auth"] == "Bearer secret-token"
