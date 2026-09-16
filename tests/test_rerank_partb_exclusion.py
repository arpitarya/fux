"""The source exclusion that turns W-154's Part B from VOID into measurable.

🔴 **The repair is one line of the harness, and the whole run rests on it.**
The first Part B was ruled
[VOID](../work/regression/2026-09-15-rerank-quality/VERDICT.md): the queries are
sentences lifted verbatim from a citing document, so that document is a perfect
proximity match and took rank 1 in **87.5 %** of contests, against the target's
3.3 %. The reranker found it and the endpoint scored that as a miss.

**A measurement tool gets a test for the same reason a shipped one does** — and
more so here, because a silent failure of the exclusion produces a filed number
shaped exactly like a clean one, which is the shape the VOID run already cost.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

import rerank_partb  # noqa: E402


def _ranked(monkeypatch, locs):
    """Make `fux ask` return `locs`, in order, without running anything."""
    monkeypatch.setattr(
        rerank_partb, "run",
        lambda tree, *a: {"results": [{"loc": l} for l in locs]},
    )


def test_the_source_is_removed_before_rank_1_is_read(monkeypatch, tmp_path):
    """The VOID run's exact case: source first, target second."""
    _ranked(monkeypatch, ["docs/GLOSSARY.md", "records/0133_predictions.md", "other.md"])
    assert rerank_partb.ask_hit(
        tmp_path, "See SR-RS decision 19.", "records/0133_predictions.md", "docs/GLOSSARY.md"
    ) is True


def test_a_genuine_rival_at_rank_1_is_still_a_miss(monkeypatch, tmp_path):
    """🔴 **The exclusion must not become a search for the target.**

    Removing one document is not the same as scanning the list for the answer.
    A rival that is not the source stays at rank 1 and the contest is a miss —
    otherwise the endpoint would reward any run where the target appears at all.
    """
    _ranked(monkeypatch, ["records/0101_cli-surface.md", "records/0133_predictions.md"])
    assert rerank_partb.ask_hit(
        tmp_path, "q", "records/0133_predictions.md", "docs/GLOSSARY.md"
    ) is False


def test_target_at_rank_1_outright_is_a_hit(monkeypatch, tmp_path):
    _ranked(monkeypatch, ["records/0133_predictions.md", "docs/GLOSSARY.md"])
    assert rerank_partb.ask_hit(
        tmp_path, "q", "records/0133_predictions.md", "docs/GLOSSARY.md"
    ) is True


def test_an_empty_list_is_a_miss_not_a_crash(monkeypatch, tmp_path):
    _ranked(monkeypatch, [])
    assert rerank_partb.ask_hit(tmp_path, "q", "t.md", "s.md") is False


def test_a_list_of_only_the_source_is_a_miss(monkeypatch, tmp_path):
    """⚠ **Why `--top` is 10 and not 1.** With a top of 1 the exclusion would
    empty the list on every source-winning contest, and *the target was second*
    would be indistinguishable from *there was no result*."""
    _ranked(monkeypatch, ["docs/GLOSSARY.md"])
    assert rerank_partb.ask_hit(tmp_path, "q", "t.md", "docs/GLOSSARY.md") is False


def test_unparseable_output_is_None_and_not_a_miss(monkeypatch, tmp_path):
    """`None` drops the contest from the paired counts; `False` would score it.

    A command that failed is not evidence the reranker missed.
    """
    monkeypatch.setattr(rerank_partb, "run", lambda tree, *a: None)
    assert rerank_partb.ask_hit(tmp_path, "q", "t.md", "s.md") is None


def _harness_source() -> str:
    return (ROOT / "tools" / "quality-controls" / "rerank_partb.py").read_text(encoding="utf-8")


def test_the_default_path_set_is_ask_alone():
    """🔴 The `answer` path is out of scope on MEASURED grounds (0 of 120), so a
    default that ran it would quietly file an INCONCLUSIVE arm beside a real one.
    """
    assert 'default=["ask"]' in _harness_source()


def test_headroom_is_measured_in_the_baseline_arm():
    """The definition the VOID run had backwards.

    *Right in both arms* reports what SURVIVED the treatment rather than what was
    AT RISK, so it shrinks exactly when an arm is breaking things.
    """
    source = _harness_source()
    assert 'regress = sum(1 for r in usable if r[f"{path}_off"])' in source
    assert 'r[f"{path}_off"] and r[f"{path}_on"]' not in source


def test_every_row_carries_the_excluded_source(tmp_path, monkeypatch):
    """The exclusion is auditable from the filed rows, never only asserted."""
    contests = tmp_path / "c.jsonl"
    contests.write_text(
        json.dumps({"query": "q", "target": "t.md", "source": "s.md", "number": "1",
                    "line_start": 1, "line_end": 2}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(rerank_partb, "set_weight", lambda tree, v: None)
    _ranked(monkeypatch, ["t.md"])
    rows = tmp_path / "rows.jsonl"
    rerank_partb.main(["--tree", str(tmp_path), "--contests", str(contests),
                       "--rows-out", str(rows)])
    row = json.loads(rows.read_text(encoding="utf-8").strip())
    assert row["source"] == "s.md"
    assert row["ask_off"] is True and row["ask_on"] is True
