"""`identifier_probe.py` — the rank arithmetic, and the two things it must not do.

The probe is the instrument W-205 part 2 measures with, and an instrument that
is wrong in the same direction on both arms hides a real effect while looking
healthy. What is checked here is the arithmetic and the refusals, never a
ranking: no `fux` process is started in this file.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "identifier_probe", ROOT / "tools" / "quality-controls" / "identifier_probe.py")
ip = importlib.util.module_from_spec(_spec)
sys.modules["identifier_probe"] = ip
_spec.loader.exec_module(ip)


LOCS = ["seed/16.md", "seed/17.md", "seed/18.md"]


# --- the arithmetic ---------------------------------------------------------

def test_rank_is_one_based_because_a_reader_counts_from_one() -> None:
    assert ip.rank_of(LOCS, "seed/16.md") == 1
    assert ip.rank_of(LOCS, "seed/18.md") == 3


def test_a_document_that_did_not_rank_is_none_not_zero() -> None:
    """🔴 `0` would sort ahead of rank 1 in every comparison downstream."""
    assert ip.rank_of(LOCS, "seed/99.md") is None


def test_first_relevant_is_the_earliest_not_the_best_named() -> None:
    assert ip.first_of(LOCS, ["seed/18.md", "seed/17.md"]) == 2
    assert ip.first_of(LOCS, ["seed/99.md"]) is None


def test_an_empty_ranked_list_is_a_miss_and_not_an_error() -> None:
    assert ip.rank_of([], "seed/16.md") is None
    assert ip.first_of([], ["seed/16.md"]) is None


# --- the summary ------------------------------------------------------------

def rows(*specs: tuple[str, int | None, int | None]) -> list[dict]:
    return [{"id": f"idq-{i:02d}", "identifier": f"X-{i}", "family": fam,
             "primary": "seed/16.md", "rank_primary_bare": bare,
             "rank_primary_question": q, "rank_relevant_question": q,
             "n_results_question": 0, "n_results_bare": 0, "top3_bare": []}
            for i, (fam, bare, q) in enumerate(specs, 1)]


def test_hit_at_k_counts_a_rank_inside_k_and_nothing_else() -> None:
    s = ip.summarise(rows(("a", 1, 1), ("a", 3, 4), ("a", 4, None), ("a", None, 2)))
    assert s["n"] == 4
    assert s["bare_hit_at_1"] == 1
    assert s["bare_hit_at_3"] == 2
    assert s["bare_miss"] == 1
    assert s["question_hit_at_3"] == 2
    assert s["question_miss"] == 1


def test_families_are_counted_apart_because_the_sibling_families_are_the_measurement() -> None:
    """A pooled number hides exactly what part 2 changes: `RF-118`/`RF-119`/
    `RF-120` colliding on one prefix is a property of that family, and an
    average over 43 rows moves by a fraction of one flip when it is fixed."""
    s = ip.summarise(rows(("sibling-rf", 1, 1), ("sibling-rf", 5, 1), ("unique", 1, 1)))
    assert s["by_family"]["sibling-rf"] == {"n": 2, "bare_hit_at_1": 1, "bare_miss": 0}
    assert s["by_family"]["unique"]["n"] == 1


def test_the_summary_states_no_verdict_and_no_threshold() -> None:
    """🔴 A floor lives in a frozen pre-registration, never in the instrument."""
    s = ip.summarise(rows(("a", 1, 1)))
    text = json.dumps(s).lower()
    for forbidden in ("pass", "fail", "verdict", "threshold", "floor", "better", "worse"):
        assert forbidden not in text


# --- the refusals -----------------------------------------------------------

def test_a_missing_index_is_refused_rather_than_measured_as_zero(tmp_path: Path, capsys) -> None:
    """An arm whose ingest failed would otherwise file 43 clean misses, which
    reads exactly like a catastrophic ranking regression."""
    rc = ip.main(["--queries", str(tmp_path / "q.jsonl"), "--rung", "rung-seed",
                  "--tree", str(tmp_path)])
    assert rc == 1
    assert "no index" in capsys.readouterr().err


def test_band_is_omitted_only_when_asked(monkeypatch) -> None:
    """v1.0.0's `ask` has no `--band` and argparse exits 2 on it; v2 and HEAD
    need it. The flag is per arm, so it is a parameter and not a constant."""
    seen: list[list[str]] = []

    class Done:
        stdout = '{"results": []}'

    monkeypatch.setattr(ip.subprocess, "run",
                        lambda cmd, **kw: seen.append(cmd) or Done())
    ip.ask("fux", Path("."), "RF-119", 20, True)
    ip.ask("fux", Path("."), "RF-119", 20, False)
    assert "--band" in seen[0] and "--band" not in seen[1]


def test_unparseable_output_is_an_empty_ranking_not_a_crash(monkeypatch) -> None:
    class Broken:
        stdout = "Traceback (most recent call last):"

    monkeypatch.setattr(ip.subprocess, "run", lambda cmd, **kw: Broken())
    assert ip.ask("fux", Path("."), "RF-119", 20, True) == []


# --- the query set itself ---------------------------------------------------

QUERIES = ROOT / "work" / "regression" / "2026-09-21-identifier-analyzer" / "evidence" / "id-queries.jsonl"


@pytest.mark.skipif(not QUERIES.is_file(), reason="the 2026-09-21 query set is not filed")
def test_every_id_query_targets_a_document_that_exists() -> None:
    """A target that moved is a miss nobody can distinguish from a ranking
    failure — and one target WAS repointed when set 3 landed."""
    seed = ROOT / "work" / "golden"
    for line in QUERIES.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        for loc in [row["primary"], *row["relevant"]]:
            assert (seed / loc).is_file(), f"{row['id']} targets {loc}, which does not exist"


@pytest.mark.skipif(not QUERIES.is_file(), reason="the 2026-09-21 query set is not filed")
def test_the_query_set_carries_no_answer_and_names_its_author() -> None:
    """🔴 An id-query set is not a golden question set. If one ever grew an
    answer field it would be a key living outside Arpit's custody (L11)."""
    for line in QUERIES.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        assert row["_AUTHOR"].startswith("Claude Code, 2026-09-21")
        assert not ({"answer", "answers", "evidence", "answerable"} & set(row))
