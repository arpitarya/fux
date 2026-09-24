"""W-220 — the index X-ray: facts, probes, the fold and `--diff`.

[SR-INSPECT](../records/0156_inspect.md) decisions 17–22. Each test here is one
line of W-220's §Tests, on a corpus small enough to reason about by hand:

- the report is byte-identical on an unchanged index, and carries no timestamp;
- every capped list ships its full count;
- a recursive walk never enters `work/golden/` (a file is planted there);
- the facts cache is reused, and a decoder bump invalidates only that decoder's
  documents while a `RULES_VERSION` bump invalidates every one;
- the probe sample is evenly spaced and labelled an estimate;
- data documents are reported on both bars, side by side;
- `--diff` names a lost edge as an alert.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from fux.inspect import as_dict, diff as diff_mod, facts as facts_mod, inspect_index, render_markdown
from fux.inspect import xray as xray_mod
from fux.inspect._scan import read_index_view

DOCS = {
    "docs/runbook.md": "# Drain the retry queue\n\nStop the consumer, then drain the retry "
    "queue and confirm the dead-letter count is zero.\n\nSee [the ledger](ledger.md).\n",
    "docs/ledger.md": "# Ledger\n\nThe ledger records every reconciliation run with its "
    "digest and the operator who approved it.\n",
    "docs/alpha.md": "# Overview\n\nAlpha covers saturation and length normalisation.\n",
    "docs/beta.md": "# Overview\n\nBeta covers fetching, digests and verification.\n",
    "docs/page.html": "<html><body><nav>Home Products Careers Contact</nav><h1>Status page</h1>"
    "<p>The status page reports incidents.</p></body></html>",
    "docs/rows-a.json": '{"rows": [{"id": 1, "name": "north depot"}]}',
    "docs/rows-b.json": '{"rows": [{"id": 2, "name": "south depot"}]}',
    # 🔴 THE PLANT: sources name `work`, and `!work/golden` excludes this. If any
    # walk in inspect reads a directory rather than the index, it shows up.
    "work/golden/sealed.md": "# Sealed\n\nzqsealedword must never appear in a report.\n",
    "work/notes.md": "# Notes\n\nOrdinary working notes about hooks and staging.\n",
}


def _ingest(root: Path) -> None:
    subprocess.run(
        [sys.executable, "-m", "fux.cli", "ingest"],
        cwd=root, capture_output=True, text=True, check=True,
    )


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("xray-corpus")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    fux = root / ".fux"
    (fux / "sources").mkdir(parents=True)
    (fux / "sources" / "dirs").write_text("docs\nwork\n!work/golden\n", encoding="utf-8")
    (fux / "pii.toml").write_text("", encoding="utf-8")
    for rel, body in DOCS.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    _ingest(root)
    return root


@pytest.fixture(scope="module")
def report(corpus):
    return inspect_index(corpus, probe_sample=0, retrieval_sample=0)


# --------------------------------------------------------------------------
# determinism and the counts


def test_the_report_is_byte_identical_on_an_unchanged_index(corpus, report) -> None:
    again = inspect_index(corpus, probe_sample=0, retrieval_sample=0)
    assert render_markdown(again) == render_markdown(report)
    assert json.dumps(as_dict(again), sort_keys=True) == json.dumps(as_dict(report), sort_keys=True)


def test_the_report_carries_no_timestamp(report) -> None:
    text = render_markdown(report) + json.dumps(as_dict(report))
    assert not re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text)


def test_every_capped_list_ships_its_full_count(corpus) -> None:
    capped = as_dict(inspect_index(corpus, probe_sample=0, retrieval_sample=0, top=1))
    assert capped["identity"]["groups"] >= len(capped["identity"]["top"])
    assert capped["triage_count"] >= len(capped["triage"])
    assert len(capped["triage"]) <= 1 < capped["triage_count"]
    assert capped["probes"]["title_miss_count"] >= len(capped["probes"]["title_misses"])


def test_a_recursive_walk_never_enters_the_golden_directory(corpus, report) -> None:
    """L11: the plant under `work/golden/` is absent from every artifact."""
    payload = json.dumps(as_dict(report)) + render_markdown(report)
    assert "work/golden" not in payload
    assert "zqsealedword" not in payload
    cache = facts_mod._path(corpus).read_text(encoding="utf-8")
    assert "work/golden" not in cache
    # …and the ordinary file beside it IS there, so the absence means something.
    assert "work/notes.md" in payload


# --------------------------------------------------------------------------
# the fold


def test_two_documents_sharing_a_title_are_named_as_an_identity_group(report) -> None:
    identity = as_dict(report)["identity"]
    titles = {row["title"]: row["count"] for row in identity["top"]}
    assert titles.get("Overview") == 2


def test_data_documents_are_reported_on_both_bars_side_by_side(report) -> None:
    """Ruled 2026-09-23: identifiable AND reachable, never averaged into one."""
    data = as_dict(report)["probes"]["data"]
    assert data["documents"] == 2
    assert set(data) == {"documents", "identifiable", "reachable", "both"}
    # The json decoder titles both by their first key — `rows` — so neither is
    # identifiable by title, which is W-220 finding 2 on a two-document corpus.
    assert data["identifiable"] == 0


def test_page_chrome_the_html_decoder_keeps_is_counted(report) -> None:
    row = next(r for r in as_dict(report)["documents"] if r["loc"] == "docs/page.html")
    assert "page chrome indexed" in row["findings"]
    assert report.facts.by_id[row["id"]]["chrome_tokens"] > 0


def test_triage_is_ordered_by_how_many_findings_then_id(report) -> None:
    rows = as_dict(report)["triage"]
    keys = [(-len(r["findings"]), r["id"]) for r in rows]
    assert keys == sorted(keys)


def test_the_headline_row_is_title_probe_reach_and_is_descriptive(report) -> None:
    row = next(c for c in as_dict(report)["checks"] if c["name"] == "title-probe reach")
    assert row["floor"] is None and row["status"] == "descriptive"
    assert "findable share" not in {c["name"] for c in as_dict(report)["checks"]}


# --------------------------------------------------------------------------
# probes


def test_the_probe_sample_is_evenly_spaced_and_labelled_an_estimate(corpus) -> None:
    sampled = inspect_index(corpus, probe_sample=2, retrieval_sample=0)
    probes = as_dict(sampled)["probes"]
    assert probes["sampled"] == 2 and probes["estimate"] is True
    assert "ESTIMATE" in render_markdown(sampled)
    view = sampled.view
    probed = sorted(i for i, d in enumerate(view.docs) if d.id in sampled.probes.by_id)
    from fux.inspect.lenses import _sample_indices

    assert probed == _sample_indices(view.n, 2)


def test_skipping_probes_reports_n_a_never_a_pass(corpus) -> None:
    skipped = as_dict(inspect_index(corpus, probe_sample=None, retrieval_sample=0))
    row = next(c for c in skipped["checks"] if c["name"] == "title-probe reach")
    assert row["status"] == "n/a" and skipped["probes"] is None


# --------------------------------------------------------------------------
# the facts cache


def test_an_unchanged_index_recomputes_no_facts(corpus, report) -> None:
    view = read_index_view(corpus)
    again = facts_mod.load_or_compute(corpus, view)
    assert again.computed == 0 and again.cached == view.n


def test_a_decoder_bump_recomputes_only_that_decoders_documents(corpus, report, monkeypatch) -> None:
    from fux.ingest import decoderdigest

    real = decoderdigest.binding_digests

    def bumped(root=None):
        out = dict(real(root))
        out[".html"] = out[".html"] + "-bumped"
        return out

    monkeypatch.setattr(decoderdigest, "binding_digests", bumped)
    view = read_index_view(corpus)
    after = facts_mod.load_or_compute(corpus, view)
    html = sum(1 for d in view.docs if d.loc.endswith(".html"))
    assert after.computed == html == 1


def test_a_rules_version_bump_recomputes_every_document(corpus, report, monkeypatch) -> None:
    from fux.ingest import extract

    monkeypatch.setattr(extract, "RULES_VERSION", extract.RULES_VERSION + 100)
    view = read_index_view(corpus)
    after = facts_mod.load_or_compute(corpus, view)
    assert after.computed == view.n


# --------------------------------------------------------------------------
# L3 — one document


def test_one_documents_xray_names_what_was_ingested_indexed_and_linked(corpus, report) -> None:
    view = read_index_view(corpus)
    x = xray_mod.document(corpus, view, "docs/runbook.md")
    assert x["ingested"]["kind"] == "prose" and x["ingested"]["passages"] >= 1
    assert x["indexed"]["fields"]["body"] > 0
    words = {w["term"] for w in x["indexed"]["words"]["body"]}
    assert "retri" in words or any(w.startswith("retr") for w in words)
    assert [link["id"] for link in x["links"]["out"]] == ["file:docs/ledger.md"]
    ledger = xray_mod.document(corpus, view, "docs/ledger.md")
    assert [link["id"] for link in ledger["links"]["in"]] == ["file:docs/runbook.md"]


def test_an_unknown_document_is_a_fux_error_not_a_traceback(corpus) -> None:
    from fux.errors import FuxError

    with pytest.raises(FuxError):
        xray_mod.document(corpus, read_index_view(corpus), "docs/nope.md")


# --------------------------------------------------------------------------
# --diff


def _row(doc_id: str, edges: list) -> dict:
    return {"id": doc_id, "loc": doc_id, "title": "t", "decoder": "prose", "kind": "prose",
            "nterms": 3, "flen": [3], "passages": 1, "word_cuts": 0, "title_shared_with": 0,
            "edges": edges, "probe": None, "findings": []}


def test_diff_names_a_lost_edge_as_an_alert() -> None:
    a = {"corpus": {"edges": 1}, "documents": [_row("file:a.md", [["ref", "file:b.md"]]), _row("file:b.md", [])]}
    b = {"corpus": {"edges": 0}, "documents": [_row("file:a.md", []), _row("file:b.md", [])]}
    out = diff_mod.compare(a, b)
    assert out["edge_loss"] == 1
    assert out["alerts"] == [{"id": "file:a.md", "lost_edges": [["ref", "file:b.md"]]}]
    assert "Edge loss — 1 edge(s)" in diff_mod.render_markdown(out, a="A", b="B")


def test_diff_of_a_report_against_itself_is_empty(report) -> None:
    payload = as_dict(report)
    out = diff_mod.compare(payload, payload)
    assert out["changed"] == [] and out["alerts"] == [] and out["added"] == out["removed"] == []


def test_diff_refuses_a_report_that_predates_per_document_rows(tmp_path) -> None:
    from fux.errors import FuxError

    old = tmp_path / "old.json"
    old.write_text(json.dumps({"corpus": {}}), encoding="utf-8")
    with pytest.raises(FuxError, match="per-document rows"):
        diff_mod.load_report(old)
