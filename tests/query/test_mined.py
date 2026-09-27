"""W-168 step 4 — corpus-mined expansion: the miner, the record, the fold, both
readers.

What the frozen bar requires of the build
([PRE-REGISTRATION](../../work/regression/2026-09-27-mined-expansion/PRE-REGISTRATION.md)
§The mechanism), one test per row:

- the pattern is the tag's, and the pair is analyzed and hashed like `terms`;
- the pairs ride the declaring document's OWN record, sorted, absent when none;
- the fold is set containment in both directions, over pairs in sorted order;
- `mined_weight = 0.0` reads no pair, so it is the engine before the key;
- the scan and the accelerator fold identically;
- a caller's `--expand` stacks, and keeps its own weight on a shared hash;
- `fux lexical` never folds;
- the Node reader folds identically.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from fux import store as store_mod
from fux.derive import accel, build
from fux.ingest.run import run
from fux.query import mined, run_query
from fux.query.expand import build as build_expansion
from fux.query.expand import stack
from fux.query.scan import query_term_hashes
from fux.tune import Tune

ENGINE = Path(__file__).resolve().parents[2]
NODE_ENTRY = ENGINE / "node" / "fux.mjs"

FILES = {
    # The declaring document: two pairs, one of them with a leading `The`.
    "docs/glossary.md": (
        "# Cold chain terms\n\n"
        "We track the Mean Kinetic Temperature (MKT) of every shipment.\n"
        "The Standard Operating Procedure (SOP) says who signs.\n"
        "Our Information Technology (IT) team owns the loggers.\n"
    ),
    # Uses only the short form.
    "docs/short.md": "# Excursion report\n\nThe MKT stayed within limits during the excursion.\n",
    # Uses only the long form.
    "docs/long.md": "# Storage review\n\nmean kinetic temperature for a storage excursion review\n",
    "docs/decoy.md": "# Decoy\n\nan excursion happened at the dock and nobody wrote it down\n",
}
for _i in range(10):
    FILES[f"docs/filler-{_i:02d}.md"] = f"# Filler {_i}\n\nfiller body text number {_i}\n"


def _corpus(root: Path, tune: str | None = None) -> Path:
    listing = root / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    for rel, text in FILES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    run(root)
    build(root)
    if tune is not None:
        (root / ".fux" / "tune.toml").write_text(tune, encoding="utf-8")
    return root


@pytest.fixture
def corpus(tmp_path):
    return _corpus(tmp_path)


def _records(root: Path) -> dict[str, dict]:
    out = {}
    for path in store_mod.iter_shard_paths(root):
        _, lines = store_mod.raw_record_lines(path)
        for line in lines:
            record = json.loads(line)
            out[record["loc"]] = record
    return out


def _h(text: str) -> tuple[str, ...]:
    return tuple(query_term_hashes(text))


def _payload(results):
    return [(r.id, round(r.score, 9)) for r in results]


# -- the miner -----------------------------------------------------------------


def test_the_pattern_is_the_frozen_tag_pattern():
    """Character for character: a different regex measures a different input."""
    assert mined.PATTERN.pattern == (
        r"\b((?:[A-Z][a-z]+[\s-]+){1,6}[A-Za-z]+)\s+\(([A-Z][A-Za-z]{1,6})\)"
    )


def test_mine_finds_pairs_drops_the_leading_the_and_skips_a_stopword_short_form():
    from fux.query.tokenize import tokenize

    pairs = mined.mine(FILES["docs/glossary.md"])
    # `(IT)` analyzes to nothing — `it` is a stopword — so it has no side to
    # fold; `The Standard …` loses its `The` (a stopword, so no hash moves).
    assert pairs == sorted([
        (tuple(tokenize("MKT")), tuple(tokenize("Mean Kinetic Temperature"))),
        (tuple(tokenize("SOP")), tuple(tokenize("Standard Operating Procedure"))),
    ])


def test_mine_is_a_function_of_the_declarations_not_their_order():
    a = "Mean Kinetic Temperature (MKT) and Standard Operating Procedure (SOP)."
    b = "Standard Operating Procedure (SOP) and Mean Kinetic Temperature (MKT). Mean Kinetic Temperature (MKT)."
    assert mined.mine(a) == mined.mine(b)


# -- the record ----------------------------------------------------------------


def test_the_pairs_ride_the_declaring_documents_own_record(corpus):
    records = _records(corpus)
    abbr = records["docs/glossary.md"]["abbr"]
    assert abbr == sorted(abbr), "sorted on the hashes"
    assert [list(_h("MKT")), list(_h("Mean Kinetic Temperature"))] in abbr
    for loc, record in records.items():
        if loc != "docs/glossary.md":
            assert "abbr" not in record, f"{loc}: absent when there is none"


def test_the_index_is_v5(corpus):
    shard = list(store_mod.iter_shard_paths(corpus))[0]
    header = json.loads(shard.read_text(encoding="utf-8").splitlines()[0])
    assert header["_format"] == "fux.index.v5"


def test_the_table_is_the_same_from_the_shards_and_from_the_plane(corpus):
    assert mined.table_from_shards(corpus) == accel.mined_table(corpus)
    assert mined.table_from_shards(corpus)


# -- the fold ------------------------------------------------------------------


def test_the_fold_goes_both_ways_and_stops_when_both_sides_are_present(corpus):
    table = mined.table_from_shards(corpus)
    assert mined.fold(table, list(_h("mkt excursion"))) == list(_h("mean kinetic temperature"))
    assert mined.fold(table, list(_h("mean kinetic temperature excursion"))) == list(_h("mkt"))
    assert mined.fold(table, list(_h("mkt mean kinetic temperature"))) == []
    assert mined.fold(table, list(_h("excursion"))) == []


def test_a_partial_long_form_folds_nothing(corpus):
    """Containment, not overlap: `kinetic` alone is not the long side."""
    table = mined.table_from_shards(corpus)
    assert mined.fold(table, list(_h("kinetic excursion"))) == []


def test_stack_keeps_the_callers_weight_on_a_shared_hash():
    q = list(_h("mkt excursion"))
    caller = build_expansion(q, list(_h("mean storage")), 0.2)
    stacked = stack(caller, list(_h("mean kinetic temperature")), 0.5)
    mean, storage = _h("mean storage")
    assert stacked.weights[mean] == 0.2, "the caller's word keeps the caller's weight"
    assert stacked.weights[storage] == 0.2
    for h in _h("kinetic temperature"):
        assert stacked.weights[h] == 0.5
    assert stacked.hashes[: len(caller.hashes)] == caller.hashes, "caller first, mined after"
    assert stacked.required == caller.required
    assert stack(caller, list(_h("mean kinetic")), 0.0) is caller


# -- the query path ------------------------------------------------------------


def test_off_reads_no_pair_and_is_the_engine_before_the_key(corpus, monkeypatch):
    """`0.0` must be byte-identical to the engine before `mined_weight` existed,
    and the cheapest proof is that the table is never opened."""

    def boom(*_a, **_k):
        raise AssertionError("the mined table was read at mined_weight = 0.0")

    monkeypatch.setattr(mined, "table_from_shards", boom)
    monkeypatch.setattr(accel, "mined_table", boom)
    for q in ("mkt excursion", "mean kinetic temperature", "excursion"):
        for force_scan in (True, False):
            results, _ = run_query(corpus, q, 10, force_scan=force_scan, tune=Tune())
            expected = _payload(results)
            from fux.query.scan import ask as scan_ask

            assert _payload(scan_ask(corpus, q, top=10)) == expected


@pytest.mark.parametrize("weight", [0.1, 0.2, 0.3, 0.5])
@pytest.mark.parametrize("q", ["mkt excursion", "mean kinetic temperature excursion", "sop"])
def test_the_scan_and_the_accelerator_fold_identically(corpus, q, weight):
    tune = Tune(mined_weight=weight)
    scan_results, path_a = run_query(corpus, q, 10, force_scan=True, tune=tune)
    fast_results, path_b = run_query(corpus, q, 10, force_scan=False, tune=tune)
    assert (path_a, path_b) == ("scan", "accelerator")
    assert _payload(fast_results) == _payload(scan_results)


def test_on_lifts_the_document_that_spells_it_the_other_way(corpus):
    off, _ = run_query(corpus, "mkt excursion", 10, tune=Tune())
    on, _ = run_query(corpus, "mkt excursion", 10, tune=Tune(mined_weight=0.5))
    score = lambda rs, loc: next(r.score for r in rs if r.loc == loc)  # noqa: E731
    assert score(on, "docs/long.md") > score(off, "docs/long.md")
    # The guard: nothing matching none of the user's own words is returned.
    assert all(r.loc != "docs/filler-00.md" for r in on)


def _cli(root: Path, *argv: str) -> list[dict]:
    env = dict(os.environ, PYTHONPATH=str(ENGINE / "src"))
    proc = subprocess.run(
        [sys.executable, "-m", "fux", *argv, "--json", "--top", "10"],
        capture_output=True, text=True, encoding="utf-8", cwd=root, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["results"]


def test_lexical_never_folds(tmp_path):
    on = _corpus(tmp_path / "on", "[ranking]\nmined_weight = 0.5\n")
    off = _corpus(tmp_path / "off", "[ranking]\nmined_weight = 0.0\n")
    q = "mkt excursion"
    strip = lambda rows: [(r["id"], round(r["score"], 9)) for r in rows]  # noqa: E731
    assert strip(_cli(on, "lexical", q)) == strip(_cli(off, "lexical", q))
    assert strip(_cli(on, "ask", q)) != strip(_cli(off, "ask", q)), "the arm moves ask"


# -- the Node reader -----------------------------------------------------------


def _node(root: Path, verb: str, query: str) -> list[dict]:
    proc = subprocess.run(
        ["node", str(NODE_ENTRY), verb, query, "--json", "--top", "10"],
        capture_output=True, text=True, encoding="utf-8", cwd=root,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["results"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH on this machine")
@pytest.mark.parametrize("tune", [None, "[ranking]\nmined_weight = 0.3\n"])
@pytest.mark.parametrize("q", ["mkt excursion", "mean kinetic temperature excursion", "sop"])
def test_the_node_reader_folds_identically(tmp_path, q, tune):
    root = _corpus(tmp_path, tune)
    for verb in ("ask", "lexical"):
        py = _cli(root, verb, q)
        nd = _node(root, verb, q)
        assert [r["id"] for r in nd] == [r["id"] for r in py], f"{verb}: order differs on {q!r}"
        for a, b in zip(py, nd, strict=True):
            assert round(a["score"], 9) == round(b["score"], 9), f"{verb} {a['id']}: score differs"
