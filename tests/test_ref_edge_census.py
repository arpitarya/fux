"""`ref_edge_census.py` — anchor-BEARING is not anchor-DISTINCTIVE, and the tool says so.

🔴 **Second strike, so a gate** ([SR-WORK-SESSION](../records/0060_WORK-session.md)
decision 13).

- **W-191 was the first.** A link feature was measured on a golden ladder with
  **0 `ref` edges on all eight rungs**, and *0 of 124 flips* was filed as a
  number before anybody counted the input. `ref_edge_census.py` was built so
  that could not recur.
- **W-168 is the second, and the tool built for the first would not have caught
  it.** On 2026-09-22 the ladder carried **61 anchor-bearing `ref` edges on
  every rung** — and **every word a linker used was already in the document it
  pointed at**. `anchored=61` reads as *the input is present*. It is not: the
  anchor field contributes only where a linker supplies vocabulary the target
  **lacks**, which is what
  `work/regression/2026-09-15-anchor-text/PRE-REGISTRATION.md` §*What the data
  must contain* row 1 asks for.

**So the property under test is the one that cost the session: a corpus can pass
every check this tool made before 2026-09-22 and still be unable to move the
feature.**

⚠ **The subtraction is hashes against hashes.** An edge's `at` keys and a
record's `terms` keys are the same hashed vocabulary, so the census stays inside
[L2](../records/0004_LAW-2-content-never-durable.md) — it opens no document and
reads no word.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

import ref_edge_census as census  # noqa: E402


def _index(tmp_path: Path, records: list[dict]) -> Path:
    index = tmp_path / ".fux" / "index"
    index.mkdir(parents=True)
    lines = [json.dumps({"_format": "fux.index.v4"})]
    lines += [json.dumps(r, sort_keys=True) for r in records]
    (index / "00.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return index


def _doc(doc_id: str, terms: list[str], edges: list[dict] | None = None) -> dict:
    return {"id": doc_id, "terms": {t: [1, 0, 0, 0, 0] for t in terms},
            "edges": edges or []}


# --- the distinction itself --------------------------------------------------

def test_an_anchor_that_repeats_the_targets_own_words_is_bearing_but_not_distinctive(tmp_path):
    """🔴 The 2026-09-22 shape: links, anchor text, and nothing to contribute."""
    index = _index(tmp_path, [
        _doc("src", ["alpha"], [{"kind": "ref", "dst": "tgt", "at": {"beta": 1}, "al": 1}]),
        _doc("tgt", ["beta", "gamma"]),
    ])
    out = census.census(index)
    assert out["ref"] == 1
    assert out["anchor_bearing"] == 1, "the edge does carry anchor text"
    assert out["anchor_distinctive_terms"] == 0, "and the target already had the word"
    assert out["anchor_distinctive_targets"] == 0


def test_an_anchor_supplying_a_word_the_target_lacks_is_distinctive(tmp_path):
    """The input the feature actually acts on."""
    index = _index(tmp_path, [
        _doc("src", ["alpha"], [{"kind": "ref", "dst": "tgt", "at": {"nickname": 1}, "al": 1}]),
        _doc("tgt", ["beta"]),
    ])
    out = census.census(index)
    assert out["anchor_bearing"] == 1
    assert out["anchor_distinctive_terms"] == 1
    assert out["anchor_distinctive_targets"] == 1
    assert out["anchor_distinctive_edges"] == 1


def test_the_target_may_live_in_another_shard(tmp_path):
    """The comparison needs every record in hand, so the census reads the whole
    index before counting. A one-pass version would call every edge distinctive
    whose target happened to be filed later."""
    index = tmp_path / ".fux" / "index"
    index.mkdir(parents=True)
    head = json.dumps({"_format": "fux.index.v4"})
    (index / "00.jsonl").write_text(
        head + "\n" + json.dumps(_doc("src", ["a"], [
            {"kind": "ref", "dst": "tgt", "at": {"beta": 1}, "al": 1}]), sort_keys=True) + "\n",
        encoding="utf-8")
    (index / "01.jsonl").write_text(
        head + "\n" + json.dumps(_doc("tgt", ["beta"]), sort_keys=True) + "\n", encoding="utf-8")
    assert census.census(index)["anchor_distinctive_terms"] == 0


def test_a_target_outside_the_index_counts_its_anchor_as_distinctive(tmp_path):
    """An edge whose `dst` is not in this index has no own-terms to subtract.
    Counting it as distinctive is the SAFE direction: it over-reports the input
    and can only cause a measurement to be attempted, never skipped."""
    index = _index(tmp_path, [
        _doc("src", ["a"], [{"kind": "ref", "dst": "missing", "at": {"beta": 1}, "al": 1}]),
    ])
    assert census.census(index)["anchor_distinctive_terms"] == 1


# --- the exit codes, which are what a run actually gates on ------------------

def test_no_ref_edges_exits_2(tmp_path, capsys):
    """W-191's corpus."""
    index = _index(tmp_path, [_doc("a", ["x"], [{"kind": "supersedes", "dst": "b"}])])
    assert census.main(["--index", str(index)]) == 2
    assert "NO `ref` EDGES" in capsys.readouterr().out


def test_links_whose_words_the_targets_already_have_exits_3(tmp_path, capsys):
    """🔴 W-168's corpus — and it passes every check exit 2 makes."""
    index = _index(tmp_path, [
        _doc("src", ["alpha"], [{"kind": "ref", "dst": "tgt", "at": {"beta": 1}, "al": 1}]),
        _doc("tgt", ["beta"]),
    ])
    assert census.main(["--index", str(index)]) == 3
    out = capsys.readouterr().out
    assert "0 ANCHOR-DISTINCTIVE TERMS" in out
    assert "NO `ref` EDGES" not in out, "the two zeros are different problems"


def test_a_corpus_with_distinctive_anchors_exits_0(tmp_path):
    index = _index(tmp_path, [
        _doc("src", ["alpha"], [{"kind": "ref", "dst": "tgt", "at": {"nickname": 1}, "al": 1}]),
        _doc("tgt", ["beta"]),
    ])
    assert census.main(["--index", str(index)]) == 0


def test_the_exit_code_does_not_judge_how_MUCH_is_enough(tmp_path):
    """⚠ One distinctive term exits 0, and on 2026-09-22 that one term was a
    FILENAME. Picking the count at which a corpus becomes adequate is a
    threshold, and a threshold lives in a frozen pre-registration, never in an
    instrument (SR-RS decision 10b). The tool reports `terms/targets`; the
    reader judges."""
    index = _index(tmp_path, [
        _doc("src", ["alpha"], [{"kind": "ref", "dst": "tgt", "at": {"junk": 1}, "al": 1}]),
        _doc("tgt", ["beta"]),
    ])
    assert census.main(["--index", str(index)]) == 0
